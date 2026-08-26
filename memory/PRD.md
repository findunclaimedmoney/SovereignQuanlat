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

## Implemented (2026-08-23, round 3)
- Customer accounts: JWT cookie auth (register/login/logout/me), bcrypt hashes, 5-attempt/15-min brute-force lockout, unique email index. Test user: delivered@resend.dev.
- Licensee Dashboard (/dashboard): licences auto-linked by checkout email (copy key + download), referral program — personal link ?ref=CODE, 2.5% monthly rebate on referred spend (verified: $499 → $12.48), lifetime stats. Checkout captures referral codes silently (?ref= + localStorage).
- Field Manual (/guide): six-step setup walkthrough with per-step AI narration (OpenAI tts-1-hd, onyx voice, mp3 cached on disk, served via FileResponse with Range support).
- Stripe env renamed to SOVEREIGN_STRIPE_KEY (platform pre-injects STRIPE_API_KEY=sk_test_emergent which shadows user key); load_dotenv override removed (deployment blocker fix).
- Admin refund console (/admin): API-key gated, orders list, refund + subscription cancel + licence revoke.

## Implemented (2026-08-23, round 4)
- Concierge upgraded to full memory architecture (ported from user's Convex/Mia project): pinned project memory core (Sovereign Quant Super Agent identity, importance 10) + private owner-verification memory (never injected into public chat) + 12-entry knowledge base (strategies, risk gates, licensing internals, installation, activation, troubleshooting, accounts, security, compliance) seeded in Mongo + per-session fact extraction (claude-haiku) + 50-message history + modes (sales/support/quant). Brain upgraded to claude-opus-4-7.
- Admin console: orders + refund/revoke, referral rebate payouts (mark-paid per code/month), Site Foundry (Python port of Mia's generateProject: gpt-5.4 generate → self-review → zip download, background task with status polling).
- Dashboard: full order history + payout history added.
- Guide: full audio-visual walkthrough video (6 narrated chapters, ffmpeg title cards + TTS audio, /api/guide/video).
- Welcome email on registration (guardrail-gated template).
- DECLINED: 3% per-trading-transaction fee — conflicts with user's own pinned memory core (no unregulated multi-tenant transaction-fee platform) and is regulated broker/exchange territory; offline software cannot meter trades server-side. Compliant monetization alternatives offered.

## Implemented (2026-08-23, round 5)
- AI Coach add-on (ATLAS): $49/month Stripe subscription (lookup ai_coach_monthly, live product created), Claude-Opus coach chat gated inside dashboard (coach_messages per user, knowledge base + memory core injected, education-only positioning), coach welcome email on fulfilment, coach branch in fulfil_order (no licence key minted), excluded from 365-day renewal reminders. Pricing page add-on card; PaymentSuccess handles non-licence orders.
- Confirmed user's re-uploaded workstation files (app.py etc.) are byte-identical to the originals already bundled in the paid download zip.

## Implemented (2026-08-23, round 6)
- Test data purge: all orders/users/chat/memory collections wiped for launch.
- Strategy Pack Store ("Armory" section): three one-time drop-in modules with REAL working code — Volatility Harvester $149, Mean Reversion Pro $149, Execution Suite $249 (live Stripe products, one-time payment mode). Instant zip download on success page + email link + dashboard listing; downloads gated to paid orders. Pack/coach orders excluded from licence renewal reminders; licences list no longer mixes pack/coach records.
- PaymentSuccess now renders three order kinds correctly (licence key / pack download / coach activation).

## Implemented (2026-08-23, round 7)
- Console bugfix: malformed PostHog inline script in public/index.html (missing closing paren, "Unexpected token ':'" on every page) — fixed; verified clean console on home/guide/login. NOTE: required frontend supervisor restart to serve updated public/index.html. Three.js deprecation warning is from platform script (emergent-main.js), not our code.
- Plain-English layer per external review: "Plain Talk" section (what it is / what it is not / who it is for + prominent no-track-record disclosure), plain-terms definitions under pricing grid (Max Capital, Strategies, "nothing here trades real money by itself"), concierge knowledge entry for non-technical visitors.

## Implemented (2026-08-23, round 8 — review recommendations adopted)
- Hero reality statement: plainly states no funds held, no trades placed, no broker/API keys/cloud needed; primary CTA now "Download Free — No Card" (public /api/download/community serving the workstation zip; paid downloads remain gated).
- "Receipts" section: sample executive tearsheet PDF (matplotlib-generated, clearly labeled ILLUSTRATIVE/synthetic) via /api/sample-tearsheet + "Behind the Desk" sole-ownership blurb. No fabricated testimonials (no real customers yet).
- FAQ section ("Asked First"): legality, real trades (no), requirements, refunds, losing money, data privacy. NOTE: FAQ states a refund-if-won't-activate policy — owner can veto/adjust.
- Concierge knowledge updated with free download, sample tearsheet, refund policy.

## Implemented (2026-08-23, round 9)
- Nav overlap hardening (user-reported on production, transient mid-load): nav now has permanent dark backdrop (not scroll-gated) and hero content has a guaranteed 72px safe zone below the nav; official hexagon logo (user-supplied) added to nav, favicon, apple-touch-icon, og:image. Stripe-side logo upload NOT possible via API (own-account restriction) — file ready at /app/sq-logo-stripe.png, user uploads in Dashboard → Settings → Branding.

## Implemented (2026-08-23, round 10)
- Login page restyled per user's Claude-designed HTML: DM Sans + Instrument Serif, gold eyebrow/italic-period headings, blue (#3B82F6) tabs/submit, rounded inputs on #0B0F14, serif brand + hexagon logo, "Software licensing only" fineprint. Auth logic/testids unchanged; register-through-page verified. NOTE: palette (blue/gold) intentionally departs from site-wide red/black brutalism — user's explicit choice.

## Backlog
- P0: Rotate LICENCE_HMAC_SECRET to user's own secret before real sales; user to claim Stripe sandbox (onboarding link shared) or provide own key (BYOK switch).
- P1: Customer portal to re-view licence keys by email; refund handling UI.
- P2: Community download counter/analytics; upgrade path Community→Professional inside app.

## Implemented (2026-08-23, round 11)
- Deployment health check PASSED (no hardcoded secrets/URLs, correct ports, CORS ok, supervisor valid, frontend+backend live-smoke-tested 200). User chose to keep current LICENCE_HMAC_SECRET for now (rotation still on backlog). Awaiting user-triggered production redeploy from Emergent dashboard so quant-checkout.emergent.host picks up the navy/gold restyle, logo, and console bugfix.

## Implemented (2026-08-23, round 12)
- Guide media investigation (user QA report: narration + video "stuck at 0:00"): NO REAL BUG. Both /api/guide/video and /api/guide/narration/{1-6} serve correctly on preview AND production (200, correct content-type, fast; all 6 TTS mp3s cached on disk AND git-tracked; mp4 served on prod despite not being git-tracked — deployment snapshots filesystem). Root cause of QA false positive: test browsers use open-source Chromium without H.264/AAC codecs → video readyState 0; narration MP3 actually plays fine (verified: readyState 4, duration 22.3s, currentTime advancing). Hardening applied to Guide.js: video preload none→metadata, in-player fallback download link for codec-less browsers. MINOR: requires redeploy to reach production (cosmetic only — prod media already works).

## Implemented (2026-08-23, round 13)
- New "How It Works" explainer video (2:02, 2.5MB, h264/aac +faststart) replacing old walkthrough at same /api/guide/video path — built per user's pasted production brief: 9 scenes (cold-open live terminal, what-it-is/isn't, tiers, unzip, install, REAL 2026-08-14 backtest log replay + equity curve reveal + run stats, kill-switch demo with deliberately lowered limit, tearsheet, close CTA). Narration: OpenAI tts-1-hd onyx via Emergent key, one clip per scene. Builder: backend/build_how_it_works_video.py (PIL frames + ffmpeg concat; audio cached in video_build/audio for fast rebuilds).
- Landing Proof section: new "Real Engine Run — 14 Aug 2026 · Free Community Tier" block with the actual terminal log excerpt, equity curve chart (/proof/equity_curve_run_2026-08-14.png, REPRESENTATIVE watermark), real stat tiles (+5.58%, Sharpe 0.288, −7.03% max DD, 652 trades, final equity $105,578.52), and hypothetical-backtest disclaimer. Equity curve shape is a constrained reconstruction (exact start/peak/trough/final from the log; maxDD verified == −7.0300%); user can later upload real equity_curve.csv to swap in the true path.

## Implemented (2026-08-26, round 14)
- MANUAL LICENCE SIGNING FLOW (user decision — private key never touches server): fulfil_order no longer mints keys; licence orders become licence_status="awaiting_manual_issue", buyer gets "order confirmed, key signed by desk within 24h" email (manual_licence_pending_email_html), owner gets ACTION REQUIRED email (owner_sign_request_email_html → OWNER_NOTIFY_EMAIL=admin@sovereignquant.com.au) with exact `python license_signing_tool.py issue --name X --tier Y --days 365` command. New admin endpoint POST /api/admin/orders/{session_id}/issue-key (X-Admin-Key): pasting the minted key stores it, marks issued, emails buyer, unlocks dashboard. Upgrade-to-Institutional flow also routes to manual signing. PaymentSuccess shows "Licence being signed" state + immediate workstation download. Renewal reminders only fire for issued keys; all concierge/memory/knowledge/guide/video copy switched HMAC→Ed25519, instant→24h (guide narrations 1+5 re-generated and cached; how-it-works video rebuilt). E2E tested: fake paid order → awaiting state → admin issue-key → issued+key visible. Test data cleaned.
- Social cut VERIFIED: /proof/sq-social-cut-9x16.mp4, 1080x1920, 36s, h264/aac, publicly downloadable — ready for FB/X/TikTok.
- Marketing honesty pass (2026-08-26): social cut + how-it-works video narration changed from "running right now" to "replaying exactly as it ran"; social b3 now says "equity curve, rebuilt from the actual run log". Numbers in both videos are from the user's REAL 2026-08-14 run log they pasted (652 trades, +5.58%, Sharpe 0.288, −7.03% DD, $105,578.52) — not invented; curve shape remains a captioned reconstruction (no CSV). Both videos rebuilt and re-verified serving.

## Implemented (2026-08-26, round 16)
- ED25519 APP SWAP COMPLETE: user generated keypair, provided PUBLIC_KEY_B64. Baked into app_v2.py (expiry-enforcing) → replaced bundle/app.py (placeholder + all HMAC gone), updated bundle/requirements.txt (requests/pyarrow/cryptography), refreshed README (Ed25519, no demo generator), rebuilt zip cleanly (no seller_only — verified by listing). Code-path verified with throwaway keypair: valid key accepted (tier + expires_on), tampered rejected, expired rejected. Live /api/download/community serves the new zip (verified by download + content inspection). Owner alert emails now include explicit --created-at <today> (workaround: signing tool has hardcoded default created_at "2026-08-26" which would miscompute expiry — recommend user patches default to date.today().isoformat()).
- AWAITING: user redeploy (pushes Ed25519 zip to prod) + user laptop e2e test (issue key with their private key → activate in downloaded app).

## Implemented (2026-08-26, round 15)
- Deployment health check PASSED (compilation, env config, CORS, supervisor, no destructive startup ops — the two flagged delete_many/delete_one are user-triggered chat-clear actions, self-excluded). User redeployed; PRODUCTION VERIFIED LIVE with all round-13/14 changes: /api/plans 200, new admin issue-key endpoint live and correctly rejecting bad keys (401), rebuilt guide video serving (2,534,348b), social cut serving at /proof/sq-social-cut-9x16.mp4 (734,325b). Manual licence-signing flow + honest-wording videos are now on sovereignquant.com.au.

## Next Tasks
1. USER ACTION: redeploy to production (pushes Ed25519 zip to sovereignquant.com.au). 2. USER ACTION: laptop e2e test — download zip, pip install -r requirements.txt (new deps), issue key via license_signing_tool.py with --created-at today, activate in app sidebar. 3. Recommend signing tool patch: default=date.today().isoformat() (currently hardcoded "2026-08-26" — breaks expiry math for keys issued later). 4. Upload logo in Stripe Dashboard → Settings → Branding (file at /app/sq-logo-stripe.png). 5. Optional: real equity_curve.csv upload. 6. Stripe KYC.
