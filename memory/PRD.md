# Sovereign Quant — Licence Sales Site PRD

## Original Problem Statement
"Sovereign Quant — quantitative trading software licence sales site. Landing page, pricing, and checkout for Professional and Institutional offline licences."

Product context: user uploaded the actual software (Streamlit-based "Sovereign Quant Super Agent Dashboard" — offline-first multi-agent quant workstation with HMAC-SHA256 licence activation, tiers: Community / Professional / Institutional).

## User Decisions (2026-08-23)
- Payments: Stripe Checkout, test mode first (Emergent claimable sandbox, Flow A). User has own Stripe key — offered BYOK switch, sandbox claim nudge given; awaiting decision.
- Licence delivery: instant on confirmation page + email via Emergent-managed Resend.
- Keys must genuinely activate the software → backend signs with the same HMAC secret as app.py (LICENCE_HMAC_SECRET in backend/.env). User advised to rotate to their own long secret before real sales.
- Pricing: Professional $499/yr, Institutional $1,999/yr (launch pricing; may raise later).
- Design: institutional dark / premium fintech, award-worthy motion (kinetic masked hero, manifesto chapters, editorial marquee, lenis, framer-motion, R3F point-sphere hero).

## Architecture
- Frontend: React (CRA/craco) + Tailwind, framer-motion, lenis, @react-three/fiber, react-fast-marquee, sonner. Pages: Landing (/), PaymentSuccess (/payment/success), PaymentCancel (/payment/cancel). Components: Nav, Hero (3D point sphere + masked line reveal), EditorialMarquee, Manifesto (numbered chapters), Pricing (+licensee dialog), Footer, Concierge (Claude chat widget, SSE).
- Backend: FastAPI + Motor (MongoDB). Routes: /api/plans, /api/payments/checkout, /api/payments/status/{id} (poll + Stripe fallback), /api/orders/{id} (licence key when paid), /api/stripe/webhook, /api/chat (Claude claude-sonnet-4-6 streaming SSE via EMERGENT_LLM_KEY).
- Stripe: USER'S OWN LIVE ACCOUNT (acct_1TVCs2EHzw6rVQI2, AU, charges_enabled) via STRIPE_API_KEY in backend/.env; Emergent sandbox deleted 2026-08-23 per user request. Catalog via setup_stripe.py (lookup keys professional_annual $49900, institutional_annual $199900, tax_code txcd_10103001) — created on live account. Sessions created with raw stripe SDK (mode=subscription; emergentintegrations StripeCheckout only supports payment mode, kept for webhook at /api/webhook/stripe). Tax is DIY on live account (no managed payments/Stripe Tax enabled). fulfil_order() is idempotent: marks paid, generates HMAC key, emails buyer; also triggered by success-page status polling (Stripe session retrieve fallback).
- Email: Emergent managed email proxy (EMERGENT_EMAIL_KEY, EMAIL_FROM_NAME="Sovereign Quant"), guardrail gate (_assert_safe_email) on every send. Recipient = Stripe customer_details.email.

## User Personas
- Independent/prop trader evaluating the workstation (Community → Professional).
- Small fund / institutional desk buyer (Institutional).

## Core Requirements (static)
1. Landing page with distinctive art direction. 2. Tier pricing with Professional/Institutional purchase. 3. Stripe checkout. 4. Offline licence key issuance compatible with app.py. 5. Instant + email key delivery.

## Implemented (2026-08-23)
- Full landing page (kinetic hero, manifesto chapters, marquee, pricing, footer, deploy instructions).
- Stripe checkout e2e: real test payment completed ($543.29 incl. 8.875% NY sales tax), redirect to fulfilment terminal showing licence key + order details.
- HMAC key generation verified against app.py's verify algorithm (valid: True).
- Claude concierge widget (streaming) with product knowledge; chat persisted in Mongo.
- Licence email on fulfilment (template + pipeline verified; fake test recipient rejected by proxy as designed).
- AI integration added per user request: Claude (claude-sonnet-4-6) via Emergent universal key.

## Implemented (2026-08-23, round 2)
- Stripe Tax: automatic_tax enabled at checkout (account head office Cloverdale WA, AU already configured); billing address required at checkout.
- Software download: /api/download/{session_id} serves sovereign-quant-workstation.zip (app.py, README, requirements, run scripts) to paid orders only (403 otherwise); download button on fulfilment page.
- Renewal reminders: daily background scanner emails licensees 30 days before their 365-day key expires (fulfilled_at window, renewal_reminded flag, branded template passes guardrail gate).
- Branding: API rename blocked (own-account limitation); logo generated at /app/sq_logo.png — user must upload in Stripe Dashboard (Settings → Branding) and rename business there.

## Backlog
- P0: Rotate LICENCE_HMAC_SECRET to user's own secret before real sales; user to claim Stripe sandbox (onboarding link shared) or provide own key (BYOK switch).
- P1: Customer portal to re-view licence keys by email; refund handling UI.
- P2: Community download counter/analytics; upgrade path Community→Professional inside app.

## Next Tasks
1. User decides sandbox-claim vs own Stripe key. 2. Post-purchase download delivery. 3. Renewal reminders. 4. Deploy + Stripe KYC.
