import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
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

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or "sk_test_emergent"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
LICENCE_SECRET = os.environ["LICENCE_HMAC_SECRET"]

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

SMP_COUNTRIES = {
    "AU", "AT", "BE", "BG", "CA", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GI", "GR", "HK", "HU", "IE", "IT", "JP", "LV", "LI", "LT", "LU",
    "MT", "NL", "NO", "PL", "PT", "RO", "SG", "SK", "SI", "ES", "SE", "CH",
    "GB", "US",
}

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

_tax_mode = None


def get_tax_mode():
    global _tax_mode
    if _tax_mode is None:
        try:
            country = stripe.Account.retrieve()["country"]
            _tax_mode = "full" if country in SMP_COUNTRIES else "calc_only"
        except stripe.error.StripeError:
            _tax_mode = "calc_only"
        logger.info(f"Stripe tax mode resolved: {_tax_mode}")
    return _tax_mode


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


async def fulfil_order(session_id: str, payment_intent=None, subscription=None, customer_email=None):
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


class CheckoutRequest(BaseModel):
    lookup_key: str
    licensee_name: str = Field(min_length=2, max_length=120)
    origin_url: str


@api_router.post("/payments/checkout")
async def create_checkout(req: CheckoutRequest):
    if req.lookup_key not in TIER_BY_LOOKUP:
        raise HTTPException(400, "Unknown licence tier")
    prices = await asyncio.to_thread(
        lambda: stripe.Price.list(lookup_keys=[req.lookup_key], active=True, limit=1).data
    )
    if not prices:
        raise HTTPException(500, f"Price not found: {req.lookup_key}")
    price = prices[0]
    kwargs = dict(
        line_items=[{"price": price.id, "quantity": 1}],
        mode="subscription" if price.recurring else "payment",
        success_url=f"{req.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{req.origin_url}/payment/cancel",
        metadata={"lookup_key": req.lookup_key, "licensee_name": req.licensee_name},
    )
    tax_mode = await asyncio.to_thread(get_tax_mode)
    if tax_mode == "full":
        try:
            session = await asyncio.to_thread(
                lambda: stripe.checkout.Session.create(**kwargs, managed_payments={"enabled": True})
            )
        except stripe.error.InvalidRequestError as e:
            msg = (e.user_message or "").lower()
            if "managed payments" in msg or "ineligible" in msg:
                session = await asyncio.to_thread(
                    lambda: stripe.checkout.Session.create(
                        **kwargs, automatic_tax={"enabled": True},
                        billing_address_collection="required",
                    )
                )
            else:
                raise
    elif tax_mode == "calc_only":
        session = await asyncio.to_thread(
            lambda: stripe.checkout.Session.create(
                **kwargs, automatic_tax={"enabled": True},
                billing_address_collection="required",
            )
        )
    else:
        session = await asyncio.to_thread(lambda: stripe.checkout.Session.create(**kwargs))

    await db.payment_transactions.insert_one({
        "session_id": session.id,
        "lookup_key": req.lookup_key,
        "licensee_name": req.licensee_name,
        "origin_url": req.origin_url,
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
                                   subscription=s.subscription, customer_email=email)
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


@api_router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    obj, t = event["data"]["object"], event["type"]
    if t == "checkout.session.completed":
        details = obj.get("customer_details") or {}
        await fulfil_order(obj["id"], payment_intent=obj.get("payment_intent"),
                           subscription=obj.get("subscription"), customer_email=details.get("email"))
    elif t == "checkout.session.async_payment_succeeded":
        details = obj.get("customer_details") or {}
        await fulfil_order(obj["id"], payment_intent=obj.get("payment_intent"),
                           subscription=obj.get("subscription"), customer_email=details.get("email"))
    elif t == "checkout.session.async_payment_failed":
        await db.payment_transactions.update_one(
            {"session_id": obj["id"]},
            {"$set": {"status": "failed", "payment_status": "failed", "updated_at": datetime.now(timezone.utc)}},
        )
    elif t == "checkout.session.expired":
        await db.payment_transactions.update_one(
            {"session_id": obj["id"]},
            {"$set": {"status": "expired", "payment_status": "expired", "updated_at": datetime.now(timezone.utc)}},
        )
    elif t == "charge.refunded":
        await db.payment_transactions.update_one(
            {"stripe_payment_intent_id": obj.get("payment_intent")},
            {"$set": {"status": "refunded", "payment_status": "refunded", "updated_at": datetime.now(timezone.utc)}},
        )
    return {"status": "ok"}


CONCIERGE_SYSTEM = """You are AXIOM, the official concierge of Sovereign Quant — an offline-first, multi-agent quantitative trading workstation sold on this site. Reply in plain text only: no markdown, no emojis, no bullet symbols. Keep answers under 80 words unless the buyer asks for detail.

Facts you know:
- Tiers: Community is free and included in the download ($50,000 max capital, 1 concurrent strategy, reports locked). Professional is $499 per year ($1,000,000 max capital, 3 concurrent strategies, walk-forward analysis, branded PDF tearsheets, signal export). Institutional is $1,999 per year ($50,000,000 max capital, 10 concurrent strategies, Monte Carlo simulation, multi-account routing, everything in Professional).
- The software is 100% offline-first: zero cloud telemetry, all agents run in-process on the buyer's machine.
- Licences are HMAC-SHA256 cryptographic keys, activated locally inside the app sidebar under Activate New Licence Key. No internet needed to activate. Duration 365 days.
- Features: natural-language multi-agent orchestrator (Data, Strategy, Risk, Reporting and Licence agents with correlation-traced logs), strategy playground (pairs statistical arbitrage with Engle-Granger cointegration, volatility-sized momentum with ADX filter, regime-gated mean reversion), non-bypassable risk gates with a kill switch (daily loss, drawdown, leverage, portfolio heat limits), branded executive tearsheets.
- Runs on Windows, Mac and Linux via run.bat or run.sh, then opens at localhost:8501. Python-based, dependencies: streamlit, pandas, numpy, matplotlib.
- Checkout is handled by Stripe; the licence key is issued instantly on the confirmation page after payment.
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
