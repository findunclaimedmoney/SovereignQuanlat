import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import bcrypt
import httpx
import jwt
import stripe
from emergentintegrations.payments.stripe.checkout import StripeCheckout
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI()
api_router = APIRouter(prefix="/api")

stripe.api_key = os.environ["SOVEREIGN_STRIPE_KEY"]
LICENCE_SECRET = os.environ["LICENCE_HMAC_SECRET"]

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

PLANS = [
    {
        "id": "community", "name": "Community", "price_usd": 0, "interval": None,
        "lookup_key": None, "max_capital": 50000, "strategies": 1,
    },
    {
        "id": "professional", "name": "Professional", "price_usd": 499, "interval": "year",
        "lookup_key": "professional_annual", "max_capital": 1000000, "strategies": 3,
    },
    {
        "id": "institutional", "name": "Institutional", "price_usd": 1999, "interval": "year",
        "lookup_key": "institutional_annual", "max_capital": 50000000, "strategies": 10,
    },
]
PLAN_BY_LOOKUP = {p["lookup_key"]: p for p in PLANS if p["lookup_key"]}
TIER_BY_LOOKUP = {k: p["name"] for k, p in PLAN_BY_LOOKUP.items()}


def generate_licence_key(licensee: str, tier: str, duration_days: int = 365) -> str:
    payload = {
        "licensee": licensee,
        "tier": tier,
        "duration": int(duration_days),
        "created_at": datetime.now(timezone.utc).date().isoformat(),
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True).encode()
    ).decode().rstrip("=")
    signature = hmac.new(LICENCE_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{payload_b64}.{signature_b64}"


_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str, reply_to: str | None = None) -> str | None:
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to or EMAIL_REPLY_TO:
        payload["contact_email"] = reply_to or EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            f"{EMAIL_BASE_URL}/api/v1/email/send",
            headers={"X-Email-Key": EMAIL_KEY},
            json=payload,
        )
    resp.raise_for_status()
    return resp.json().get("id")


def licence_email_html(licensee: str, tier: str, licence_key: str, success_url: str) -> str:
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#050505;padding:32px 0"><tr><td align="center">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        'style="background:#0A0A0A;border:1px solid #26262b;font-family:Courier New,monospace">'
        '<tr><td style="padding:24px 32px;border-bottom:1px solid #26262b">'
        '<span style="color:#F5F5F0;font-size:16px;font-weight:bold;letter-spacing:2px">SOVEREIGN'
        '<span style="color:#FF3333">//</span>QUANT</span></td></tr>'
        '<tr><td style="padding:32px">'
        f'<p style="color:#F5F5F0;font-size:15px;margin:0 0 8px">Licence issued, {escape(licensee)}.</p>'
        f'<p style="color:#8C8C94;font-size:13px;line-height:1.7;margin:0 0 24px">Your '
        f'<strong style="color:#F5F5F0">{escape(tier)}</strong> licence (365 days) is active. '
        'Paste the key below into the workstation sidebar under '
        '<strong style="color:#F5F5F0">Activate New Licence Key</strong>. '
        'Activation is fully offline — store this key somewhere safe.</p>'
        f'<p style="background:#050505;border:1px solid #26262b;color:#00FF66;font-size:12px;'
        f'line-height:1.8;word-break:break-all;padding:16px;margin:0 0 24px">{escape(licence_key)}</p>'
        f'<p style="margin:0 0 8px"><a href="{escape(success_url)}" '
        'style="color:#FF3333;font-size:13px">View your fulfilment terminal</a></p>'
        '<p style="color:#55555C;font-size:11px;line-height:1.7;margin:24px 0 0">Sent by '
        f'{escape(EMAIL_FROM_NAME)}. Sovereign Quant is analytical software, not financial advice. '
        'We never ask for passwords or card details by email.</p>'
        '</td></tr></table></td></tr></table>'
    )


async def fulfil_order(session_id: str, payment_intent=None, subscription=None, customer_email=None, customer=None):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn or txn.get("payment_status") == "paid":
        return
    tier = TIER_BY_LOOKUP.get(txn.get("lookup_key"), "Professional")
    licensee = txn.get("licensee_name") or "Licensee"
    licence_key = generate_licence_key(licensee, tier)
    result = await db.payment_transactions.update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {
            "status": "completed", "payment_status": "paid", "tier": tier,
            "licence_key": licence_key, "licence_duration_days": 365,
            "stripe_payment_intent_id": payment_intent,
            "stripe_subscription_id": subscription,
            "stripe_customer_id": customer,
            "fulfilled_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    if result.modified_count == 0:
        return
    if customer_email:
        origin = txn.get("origin_url", "")
        success_url = f"{origin}/payment/success?session_id={session_id}"
        try:
            email_id = await send_email(
                to=customer_email,
                subject=f"Your Sovereign Quant {tier} licence key",
                html=licence_email_html(licensee, tier, licence_key, success_url),
            )
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"licence_email_id": email_id, "licence_email_to": customer_email}},
            )
        except Exception:
            logger.exception(f"Licence email failed for session {session_id}")


@api_router.get("/")
async def root():
    return {"message": "Sovereign Quant licensing API", "status": "active"}


@api_router.get("/plans")
async def get_plans():
    return {"plans": PLANS}


# ---------------------------------------------------------------------------
# Customer accounts (JWT cookie auth), dashboard, referral engine, guide audio
# ---------------------------------------------------------------------------
from fastapi.responses import Response

JWT_ALGORITHM = "HS256"
AUDIO_CACHE = ROOT_DIR / "audio_cache"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


def _set_auth_cookie(response: Response, token: str):
    response.set_cookie(key="access_token", value=token, httponly=True, secure=True,
                        samesite="none", max_age=1800, path="/")


def _public_user(user: dict) -> dict:
    return {"user_id": user["user_id"], "email": user["email"],
            "name": user.get("name"), "referral_code": user.get("referral_code")}


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@api_router.post("/auth/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "An account with this email already exists")
    user = {
        "user_id": str(uuid.uuid4()),
        "email": email,
        "name": req.name.strip(),
        "password_hash": hash_password(req.password),
        "referral_code": "SQ-" + secrets.token_hex(3).upper(),
        "role": "customer",
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    _set_auth_cookie(response, create_access_token(user["user_id"], email))
    return _public_user(user)


@api_router.post("/auth/login")
async def login(req: LoginRequest, request: Request, response: Response):
    email = req.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("count", 0) >= 5:
        last = attempt.get("last")
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last and (datetime.now(timezone.utc) - last).total_seconds() < 900:
            raise HTTPException(429, "Too many failed attempts — locked for 15 minutes")
        await db.login_attempts.delete_one({"identifier": identifier})
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last": datetime.now(timezone.utc)}},
            upsert=True,
        )
        raise HTTPException(401, "Invalid email or password")
    await db.login_attempts.delete_one({"identifier": identifier})
    _set_auth_cookie(response, create_access_token(user["user_id"], email))
    return _public_user(user)


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"status": "ok"}


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid or expired token")
    user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user


@api_router.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return _public_user(user)


@app.on_event("startup")
async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")


@api_router.get("/me/overview")
async def me_overview(user=Depends(get_current_user)):
    paid = await db.payment_transactions.find(
        {"licence_email_to": user["email"], "payment_status": "paid"}, {"_id": 0}
    ).sort("fulfilled_at", -1).to_list(50)
    licences = [{
        "session_id": o["session_id"],
        "tier": o.get("tier"),
        "licensee": o.get("licensee_name"),
        "licence_key": o.get("licence_key"),
        "revoked": bool(o.get("licence_revoked")),
    } for o in paid]
    referrals = await db.payment_transactions.find(
        {"referral_code": user.get("referral_code"), "payment_status": "paid"}, {"_id": 0}
    ).to_list(500)
    now = datetime.now(timezone.utc)

    def in_current_month(o):
        ts = o.get("fulfilled_at") or o.get("created_at")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return bool(ts) and ts.year == now.year and ts.month == now.month

    month_spend = sum(o.get("amount", 0.0) for o in referrals if in_current_month(o))
    lifetime_spend = sum(o.get("amount", 0.0) for o in referrals)
    return {
        "user": _public_user(user),
        "licences": licences,
        "referral": {
            "code": user.get("referral_code"),
            "referred_count": len(referrals),
            "month_spend": month_spend,
            "month_rebate": month_spend * 0.025,
            "lifetime_spend": lifetime_spend,
            "lifetime_rebate": lifetime_spend * 0.025,
        },
    }


GUIDE_NARRATIONS = {
    "1": "Step one. Acquire your licence. Head to the pricing section and choose Professional or Institutional. Enter the licensee name exactly as it should appear inside the workstation — it is cryptographically signed into your key. Complete checkout with Stripe, and your H M A C key appears instantly on the confirmation page, with a copy emailed to you as backup.",
    "2": "Step two. Download the workstation. On the same confirmation page, press Download Workstation. You will receive a zip archive containing the dashboard application, the dependency list, and one-command launchers for Windows, Mac, and Linux. Unpack it anywhere on your machine — it runs entirely where you put it.",
    "3": "Step three. Install dependencies. Open a terminal inside the unpacked folder. You need Python 3.10 or newer. Run: pip install, minus r, requirements dot txt. That single command pulls in Streamlit, Pandas, NumPy, and Matplotlib — everything the engine needs.",
    "4": "Step four. Launch the engine. Run the launcher for your platform — run dot b a t on Windows, or dot slash run dot s h on Mac and Linux. The workstation boots fully offline and opens in your browser at localhost, port 8501. Nothing leaves your machine. No telemetry, no cloud.",
    "5": "Step five. Activate offline. In the sidebar, open Licence Management, then Activate New Licence Key. Paste the key from your confirmation page and press Activate locally. Verification is pure H M A C cryptography — no internet call, no phone home. Your tier unlocks instantly.",
    "6": "Step six. Operate. Dispatch natural-language goals in the Orchestrator and watch the agents coordinate. Tune strategies in the Playground. Every order passes through non-bypassable risk gates — breach your drawdown limit and the kill switch locks the machine. Compile branded tearsheets from the Reports tab. Welcome to Sovereign Quant.",
}


@api_router.get("/guide/narration/{step_id}")
async def guide_narration(step_id: str):
    text = GUIDE_NARRATIONS.get(step_id)
    if not text:
        raise HTTPException(404, "Unknown guide step")
    key = hashlib.sha256(f"{text}|onyx|1.0|tts-1-hd|mp3".encode()).hexdigest()
    path = AUDIO_CACHE / f"{key}.mp3"
    if not path.exists():
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        tts = OpenAITextToSpeech(api_key=os.environ["EMERGENT_LLM_KEY"])
        audio = await tts.generate_speech(text=text, model="tts-1-hd", voice="onyx")
        path.write_bytes(audio)
    return FileResponse(path, media_type="audio/mpeg")


class CheckoutRequest(BaseModel):
    lookup_key: str
    licensee_name: str = Field(min_length=2, max_length=120)
    origin_url: str
    referral_code: Optional[str] = None


@api_router.post("/payments/checkout")
async def create_checkout(req: CheckoutRequest, request: Request):
    if req.lookup_key not in TIER_BY_LOOKUP:
        raise HTTPException(400, "Unknown licence tier")
    prices = await asyncio.to_thread(
        lambda: stripe.Price.list(lookup_keys=[req.lookup_key], active=True, limit=1).data
    )
    if not prices:
        raise HTTPException(500, f"Price not found: {req.lookup_key}")
    price = prices[0]
    session = await asyncio.to_thread(
        lambda: stripe.checkout.Session.create(
            line_items=[{"price": price.id, "quantity": 1}],
            mode="subscription" if price.recurring else "payment",
            automatic_tax={"enabled": True},
            billing_address_collection="required",
            success_url=f"{req.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{req.origin_url}/payment/cancel",
            metadata={"lookup_key": req.lookup_key, "licensee_name": req.licensee_name},
        )
    )
    await db.payment_transactions.insert_one({
        "session_id": session.id,
        "lookup_key": req.lookup_key,
        "licensee_name": req.licensee_name,
        "origin_url": req.origin_url,
        "referral_code": req.referral_code,
        "amount": float(price.unit_amount or 0) / 100.0,
        "currency": price.currency,
        "status": "initiated", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    return {"checkout_url": session.url, "session_id": session.id}


@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    record = await db.payment_transactions.find_one({"session_id": session_id})
    if not record:
        raise HTTPException(404, "Transaction not found")
    if record.get("payment_status") != "paid":
        try:
            s = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
            if s.payment_status == "paid" or s.status == "complete":
                email = s.customer_details.email if s.customer_details else None
                await fulfil_order(session_id, payment_intent=s.payment_intent,
                                   subscription=s.subscription, customer_email=email,
                                   customer=s.customer)
                record = await db.payment_transactions.find_one({"session_id": session_id})
        except stripe.error.StripeError:
            pass
    return {
        "session_id": record["session_id"],
        "status": record["status"],
        "payment_status": record["payment_status"],
    }


@api_router.get("/orders/{session_id}")
async def get_order(session_id: str):
    record = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not record:
        raise HTTPException(404, "Order not found")
    if record.get("payment_status") != "paid":
        return {
            "session_id": session_id,
            "status": record.get("status"),
            "payment_status": record.get("payment_status"),
        }
    plan = PLAN_BY_LOOKUP.get(record.get("lookup_key"), {})
    return {
        "session_id": session_id,
        "status": "completed",
        "payment_status": "paid",
        "tier": record.get("tier"),
        "licensee": record.get("licensee_name"),
        "licence_key": record.get("licence_key"),
        "duration_days": record.get("licence_duration_days", 365),
        "max_capital": plan.get("max_capital"),
        "strategies": plan.get("strategies"),
        "amount": record.get("amount"),
        "currency": record.get("currency"),
    }


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    host_url = str(request.base_url)
    stripe_checkout = StripeCheckout(
        api_key=os.environ["SOVEREIGN_STRIPE_KEY"],
        webhook_url=f"{host_url}api/webhook/stripe",
    )
    webhook_response = await stripe_checkout.handle_webhook(
        body, request.headers.get("Stripe-Signature")
    )
    t = webhook_response.event_type
    session_id = webhook_response.session_id
    if t in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        s = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
        email = s.customer_details.email if s.customer_details else None
        await fulfil_order(session_id, payment_intent=s.payment_intent,
                           subscription=s.subscription, customer_email=email,
                           customer=s.customer)
    elif t == "checkout.session.async_payment_failed":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "failed", "payment_status": "failed", "updated_at": datetime.now(timezone.utc)}},
        )
    elif t == "checkout.session.expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "expired", "payment_status": "expired", "updated_at": datetime.now(timezone.utc)}},
        )
    return {"status": "ok"}


BUNDLE_ZIP = ROOT_DIR / "sovereign-quant-workstation.zip"


@api_router.get("/download/{session_id}")
async def download_workstation(session_id: str):
    record = await db.payment_transactions.find_one({"session_id": session_id})
    if not record or record.get("payment_status") != "paid":
        raise HTTPException(403, "A paid licence is required to download the workstation")
    return FileResponse(BUNDLE_ZIP, filename="sovereign-quant-workstation.zip", media_type="application/zip")


def renewal_email_html(licensee: str, tier: str, origin: str) -> str:
    renew_url = f"{origin}/#pricing"
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#050505;padding:32px 0"><tr><td align="center">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        'style="background:#0A0A0A;border:1px solid #26262b;font-family:Courier New,monospace">'
        '<tr><td style="padding:24px 32px;border-bottom:1px solid #26262b">'
        '<span style="color:#F5F5F0;font-size:16px;font-weight:bold;letter-spacing:2px">SOVEREIGN'
        '<span style="color:#FF3333">//</span>QUANT</span></td></tr>'
        '<tr><td style="padding:32px">'
        f'<p style="color:#F5F5F0;font-size:15px;margin:0 0 8px">30 days left, {escape(licensee)}.</p>'
        f'<p style="color:#8C8C94;font-size:13px;line-height:1.7;margin:0 0 24px">Your '
        f'<strong style="color:#F5F5F0">{escape(tier)}</strong> licence expires in 30 days. '
        'Renew now and a fresh 365-day HMAC key is issued instantly — activation takes '
        'seconds in the workstation sidebar.</p>'
        f'<p style="margin:0 0 8px"><a href="{escape(renew_url)}" '
        'style="color:#FF3333;font-size:13px">Renew your licence</a></p>'
        '<p style="color:#55555C;font-size:11px;line-height:1.7;margin:24px 0 0">Sent by '
        f'{escape(EMAIL_FROM_NAME)}. We never ask for passwords or card details by email.</p>'
        '</td></tr></table></td></tr></table>'
    )


async def renewal_reminder_loop():
    await asyncio.sleep(60)
    while True:
        try:
            now = datetime.now(timezone.utc)
            window = {"$gte": now - timedelta(days=336), "$lte": now - timedelta(days=334)}
            cursor = db.payment_transactions.find({
                "payment_status": "paid",
                "renewal_reminded": {"$ne": True},
                "fulfilled_at": window,
            })
            async for txn in cursor:
                email = txn.get("licence_email_to")
                if not email:
                    continue
                try:
                    await send_email(
                        to=email,
                        subject=f"Your Sovereign Quant {txn.get('tier')} licence expires in 30 days",
                        html=renewal_email_html(
                            txn.get("licensee_name") or "Licensee",
                            txn.get("tier") or "Professional",
                            txn.get("origin_url", ""),
                        ),
                    )
                    await db.payment_transactions.update_one(
                        {"session_id": txn["session_id"]},
                        {"$set": {"renewal_reminded": True}},
                    )
                    logger.info(f"Renewal reminder sent for {txn['session_id']}")
                except Exception:
                    logger.exception(f"Renewal reminder failed for {txn['session_id']}")
        except Exception:
            logger.exception("Renewal reminder scan failed")
        await asyncio.sleep(24 * 3600)


@app.on_event("startup")
async def start_renewal_reminders():
    asyncio.create_task(renewal_reminder_loop())


async def require_admin(request: Request):
    ip = request.client.host if request.client else "unknown"
    attempt = await db.admin_attempts.find_one({"identifier": ip})
    if attempt and attempt.get("count", 0) >= 5:
        last = attempt.get("last")
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last and (datetime.now(timezone.utc) - last).total_seconds() < 900:
            raise HTTPException(429, "Too many failed attempts — locked for 15 minutes")
        await db.admin_attempts.delete_one({"identifier": ip})
    key = request.headers.get("X-Admin-Key", "")
    if not hmac.compare_digest(key, os.environ["ADMIN_API_KEY"]):
        await db.admin_attempts.update_one(
            {"identifier": ip},
            {"$inc": {"count": 1}, "$set": {"last": datetime.now(timezone.utc)}},
            upsert=True,
        )
        raise HTTPException(401, "Invalid admin key")
    await db.admin_attempts.delete_one({"identifier": ip})


@api_router.get("/admin/orders")
async def admin_list_orders(admin=Depends(require_admin)):
    orders = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    for o in orders:
        for k in ("created_at", "updated_at", "fulfilled_at"):
            if isinstance(o.get(k), datetime):
                o[k] = o[k].isoformat()
    return {"orders": orders}


@api_router.post("/admin/orders/{session_id}/refund")
async def admin_refund_order(session_id: str, admin=Depends(require_admin)):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(404, "Order not found")
    if txn.get("payment_status") != "paid":
        raise HTTPException(400, "Only paid orders can be refunded")
    refunded = False
    pi = txn.get("stripe_payment_intent_id")
    try:
        if pi:
            await asyncio.to_thread(stripe.Refund.create, payment_intent=pi)
            refunded = True
        elif txn.get("stripe_customer_id"):
            charges = await asyncio.to_thread(
                lambda: stripe.Charge.list(customer=txn["stripe_customer_id"], limit=10).data
            )
            paid = [c for c in charges if c.status == "succeeded" and not c.refunded]
            if paid:
                await asyncio.to_thread(stripe.Refund.create, charge=paid[0].id)
                refunded = True
    except stripe.error.StripeError as e:
        raise HTTPException(502, f"Stripe refund failed: {e.user_message or str(e)}")
    if not refunded:
        raise HTTPException(400, "No refundable payment found on Stripe")
    sub = txn.get("stripe_subscription_id")
    if sub:
        try:
            await asyncio.to_thread(stripe.Subscription.cancel, sub)
        except stripe.error.StripeError:
            pass
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": "refunded", "payment_status": "refunded", "licence_revoked": True,
                  "updated_at": datetime.now(timezone.utc)}},
    )
    return {"status": "refunded"}


def portal_email_html(orders, origin: str) -> str:
    rows = ""
    for o in orders:
        url = f"{origin}/payment/success?session_id={o['session_id']}"
        rows += (
            '<tr><td style="padding:16px 0;border-top:1px solid #26262b">'
            f'<p style="color:#F5F5F0;font-size:13px;margin:0 0 6px">'
            f'{escape(o.get("tier") or "Licence")} — {escape(o.get("licensee_name") or "")}</p>'
            '<p style="background:#050505;border:1px solid #26262b;color:#00FF66;font-size:11px;'
            f'line-height:1.7;word-break:break-all;padding:12px;margin:0 0 8px">{escape(o.get("licence_key") or "")}</p>'
            f'<p style="margin:0"><a href="{escape(url)}" style="color:#FF3333;font-size:12px">'
            'Open fulfilment terminal (key + workstation download)</a></p></td></tr>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#050505;padding:32px 0"><tr><td align="center">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        'style="background:#0A0A0A;border:1px solid #26262b;font-family:Courier New,monospace">'
        '<tr><td style="padding:24px 32px;border-bottom:1px solid #26262b">'
        '<span style="color:#F5F5F0;font-size:16px;font-weight:bold;letter-spacing:2px">SOVEREIGN'
        '<span style="color:#FF3333">//</span>QUANT</span></td></tr>'
        '<tr><td style="padding:32px">'
        '<p style="color:#F5F5F0;font-size:15px;margin:0 0 8px">Your licence vault.</p>'
        '<p style="color:#8C8C94;font-size:13px;line-height:1.7;margin:0">Every paid licence '
        'registered to this email is below. Activation is fully offline.</p>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>'
        '<p style="color:#55555C;font-size:11px;line-height:1.7;margin:24px 0 0">Sent by '
        f'{escape(EMAIL_FROM_NAME)}. If you did not request this, ignore it. '
        'We never ask for passwords or card details by email.</p>'
        '</td></tr></table></td></tr></table>'
    )


class PortalRecoverRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)


@api_router.post("/portal/recover")
async def portal_recover(req: PortalRecoverRequest):
    email = req.email.strip().lower()
    recent = await db.portal_sends.find_one({"email": email})
    if recent:
        sent_at = recent["sent_at"]
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - sent_at).total_seconds() < 600:
            return {"status": "ok"}
    orders = await db.payment_transactions.find(
        {"licence_email_to": email, "payment_status": "paid"}, {"_id": 0}
    ).to_list(20)
    if orders:
        try:
            await send_email(
                to=email,
                subject="Your Sovereign Quant licence keys",
                html=portal_email_html(orders, orders[0].get("origin_url", "")),
            )
            await db.portal_sends.update_one(
                {"email": email}, {"$set": {"sent_at": datetime.now(timezone.utc)}}, upsert=True
            )
        except Exception:
            logger.exception("Portal recovery email failed")
    return {"status": "ok"}


class UpgradeRequest(BaseModel):
    session_id: str


@api_router.post("/upgrades")
async def upgrade_to_institutional(req: UpgradeRequest):
    txn = await db.payment_transactions.find_one({"session_id": req.session_id})
    if not txn or txn.get("payment_status") != "paid":
        raise HTTPException(404, "Paid order not found")
    if txn.get("tier") != "Professional":
        raise HTTPException(400, "Only Professional licences can be upgraded")
    sub_id = txn.get("stripe_subscription_id")
    if not sub_id:
        raise HTTPException(400, "No active subscription on this order")
    prices = await asyncio.to_thread(
        lambda: stripe.Price.list(lookup_keys=["institutional_annual"], active=True, limit=1).data
    )
    if not prices:
        raise HTTPException(500, "Institutional price not found")
    sub = await asyncio.to_thread(stripe.Subscription.retrieve, sub_id)
    item_id = sub["items"].data[0].id
    sub = await asyncio.to_thread(
        lambda: stripe.Subscription.modify(
            sub_id,
            items=[{"id": item_id, "price": prices[0].id}],
            proration_behavior="always_invoice",
        )
    )
    paid = True
    latest = getattr(sub, "latest_invoice", None)
    if latest:
        inv = await asyncio.to_thread(stripe.Invoice.retrieve, latest)
        if inv.status != "paid":
            try:
                inv = await asyncio.to_thread(stripe.Invoice.pay, latest)
            except stripe.error.StripeError:
                pass
        paid = inv.status == "paid"
    if not paid:
        return {"status": "pending_payment"}
    new_key = generate_licence_key(txn.get("licensee_name") or "Licensee", "Institutional")
    await db.payment_transactions.update_one(
        {"session_id": req.session_id},
        {"$set": {"tier": "Institutional", "licence_key": new_key, "upgraded_from": "Professional",
                  "upgraded_at": datetime.now(timezone.utc)}},
    )
    email = txn.get("licence_email_to")
    if email:
        origin = txn.get("origin_url", "")
        try:
            await send_email(
                to=email,
                subject="Your Sovereign Quant Institutional licence key",
                html=licence_email_html(
                    txn.get("licensee_name") or "Licensee", "Institutional", new_key,
                    f"{origin}/payment/success?session_id={req.session_id}",
                ),
            )
        except Exception:
            logger.exception(f"Upgrade email failed for {req.session_id}")
    return {"status": "upgraded", "tier": "Institutional"}


CONCIERGE_SYSTEM = """You are AXIOM, the official concierge of Sovereign Quant — an offline-first, multi-agent quantitative trading workstation sold on this site. Reply in plain text only: no markdown, no emojis, no bullet symbols. Keep answers under 80 words unless the buyer asks for detail.

Facts you know:
- Tiers: Community is free and included in the download ($50,000 max capital, 1 concurrent strategy, reports locked). Professional is $499 per year ($1,000,000 max capital, 3 concurrent strategies, walk-forward analysis, branded PDF tearsheets, signal export). Institutional is $1,999 per year ($50,000,000 max capital, 10 concurrent strategies, Monte Carlo simulation, multi-account routing, everything in Professional).
- The software is 100% offline-first: zero cloud telemetry, all agents run in-process on the buyer's machine.
- Licences are HMAC-SHA256 cryptographic keys, activated locally inside the app sidebar under Activate New Licence Key. No internet needed to activate. Duration 365 days.
- Features: natural-language multi-agent orchestrator (Data, Strategy, Risk, Reporting and Licence agents with correlation-traced logs), strategy playground (pairs statistical arbitrage with Engle-Granger cointegration, volatility-sized momentum with ADX filter, regime-gated mean reversion), non-bypassable risk gates with a kill switch (daily loss, drawdown, leverage, portfolio heat limits), branded executive tearsheets.
- Runs on Windows, Mac and Linux via run.bat or run.sh, then opens at localhost:8501. Python-based, dependencies: streamlit, pandas, numpy, matplotlib.
- Checkout is handled by Stripe; the licence key is issued instantly on the confirmation page after payment, and the full workstation files (app.py, run scripts, README) can be downloaded from that same page.
- Customers can create a free account (Sign In page) to access the Licensee Dashboard: view and copy their licence keys, re-download the workstation, and manage referrals. Licences appear automatically when the checkout email matches the account email.
- Referral program: every account gets a referral link. The referrer earns a 2.5% rebate on everything their referrals spend each month, tracked live in the dashboard.
- The Field Manual (guide page) is a six-step audio-narrated walkthrough: acquire licence, download, install dependencies, launch, offline activation, operate.
- The Buyer Portal emails licence keys to any buyer who enters their purchase email.
- Never give financial advice, never promise returns, never discuss competitors. If asked something unrelated to the product, redirect to Sovereign Quant."""


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=4, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


@api_router.post("/chat")
async def concierge_chat(req: ChatRequest):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

    history = await db.concierge_messages.find(
        {"session_id": req.session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(24)
    transcript = "\n".join(
        ("Buyer: " if m["role"] == "user" else "Concierge: ") + m["content"]
        for m in history[-12:]
    )
    prompt = f"Conversation so far:\n{transcript}\n\nBuyer: {req.message}" if transcript else req.message
    await db.concierge_messages.insert_one({
        "session_id": req.session_id, "role": "user", "content": req.message,
        "created_at": datetime.now(timezone.utc),
    })

    async def event_generator():
        chat = LlmChat(
            api_key=os.environ["EMERGENT_LLM_KEY"],
            session_id=f"concierge-{req.session_id}",
            system_message=CONCIERGE_SYSTEM,
        ).with_model("anthropic", "claude-sonnet-4-6")
        full = []
        try:
            async for ev in chat.stream_message(UserMessage(text=prompt)):
                if isinstance(ev, TextDelta):
                    full.append(ev.content)
                    yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception:
            logger.exception("Concierge stream failed")
            if not full:
                yield f"data: {json.dumps({'delta': 'CONNECTION FAULT — please retransmit.'})}\n\n"
        if full:
            await db.concierge_messages.insert_one({
                "session_id": req.session_id, "role": "assistant",
                "content": "".join(full), "created_at": datetime.now(timezone.utc),
            })
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
