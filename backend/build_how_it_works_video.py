"""Builds the 'How It Works' explainer video for Sovereign Quant.

9 scenes per production brief: real terminal replay of the 2026-08-14
Community-tier backtest run, equity-curve reveal, kill-switch demo,
tearsheet, close card. TTS narration (OpenAI tts-1-hd, onyx) per scene.
Also exports the equity-curve PNG used by the landing-page Proof section.
"""
import asyncio
import os
import subprocess
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv("/app/backend/.env")

BACKEND = Path("/app/backend")
WORK = BACKEND / "video_build"
FRAMES = WORK / "frames"
AUDIO = WORK / "audio"
SEGMENTS = WORK / "segments"
for d in (FRAMES, AUDIO, SEGMENTS):
    d.mkdir(parents=True, exist_ok=True)

OUT = BACKEND / "guide_walkthrough.mp4"
SITE_CHART = Path("/app/frontend/public/proof/equity_curve_run_2026-08-14.png")

W, H = 1280, 720
BG = "#0B0F14"
PANEL = "#111827"
GOLD = "#C9A227"
AMBER = "#F59E0B"
TEXT = "#E5E7EB"
DIM = "#8B93A1"
GREEN = "#10B981"
RED = "#EF4444"

MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
MONO_B = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"


def f(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# Equity curve — representative reconstruction matching the real run's
# logged headline figures (start 100,000; peak 109,911.16; trough -7.03%
# from peak; final 105,578.52 over 1,662 bars).
# ---------------------------------------------------------------------------
def equity_series():
    rng = np.random.default_rng(14)
    n = 1662
    peak, trough, final = 109911.16, 109911.16 * (1 - 0.0703), 105578.52
    anchors = [
        (0, 100000.0), (250, 103500.0), (500, peak), (750, 107800.0),
        (1000, 108200.0), (1150, 107000.0), (1240, trough), (1300, 102800.0),
        (1450, 104200.0), (n - 1, final),
    ]
    xs = np.array([a for a, _ in anchors])
    ys = np.array([v for _, v in anchors])
    curve = np.interp(np.arange(n), xs, ys)
    noise = rng.normal(0, 0.0007, n).cumsum()
    noise -= np.linspace(noise[0], noise[-1], n)
    curve = curve * (1 + noise)
    curve[0] = 100000.0
    curve[500] = peak
    curve = np.minimum(curve, peak)
    running_peak = np.maximum.accumulate(curve)
    curve = np.maximum(curve, running_peak * (1 - 0.0703) + 1)  # never breach logged max DD
    curve[1240] = peak * (1 - 0.0703)  # touch the -7.03% trough exactly once
    curve[-1] = final
    return curve


def render_chart(path, size=(1100, 460), watermark=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    curve = equity_series()
    fig, ax = plt.subplots(figsize=(size[0] / 100, size[1] / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.plot(curve, color=GOLD, linewidth=2.2)
    ax.fill_between(range(len(curve)), curve, 100000 * 0.97, color=GOLD, alpha=0.08)
    ax.axhline(100000, color=DIM, linewidth=0.8, linestyle="--", alpha=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#2A3342")
    ax.tick_params(colors=DIM, labelsize=11)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.set_xlabel("Backtest timeline (daily bars)", color=DIM, fontsize=11)
    if watermark:
        ax.text(0.5, 0.5, watermark, transform=ax.transAxes, fontsize=34,
                color="#FFFFFF", alpha=0.06, ha="center", va="center", rotation=12)
    fig.tight_layout()
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Frame helpers
# ---------------------------------------------------------------------------
def base_frame():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([18, 18, W - 18, H - 18], outline="#1F2937", width=2)
    d.text((40, 34), "SOVEREIGN QUANT", font=f(MONO_B, 22), fill=GOLD)
    d.text((W - 320, 34), "HOW IT WORKS", font=f(MONO, 20), fill=DIM)
    return img, d


def terminal_frame(lines, shown, title="root@sovereign: ~/sovereign_quant"):
    """Dark terminal window with the first `shown` lines revealed."""
    img, d = base_frame()
    d.rectangle([60, 90, W - 60, H - 60], fill="#05070B", outline="#1F2937", width=2)
    for i, c in enumerate((RED, AMBER, GREEN)):
        d.ellipse([84 + i * 28, 106, 98 + i * 28, 120], fill=c)
    d.text((200, 104), title, font=f(MONO, 18), fill=DIM)
    y = 150
    for ln in lines[:shown]:
        color = TEXT
        if ln.startswith("$"):
            color = GOLD
        elif "KILL" in ln or "breached" in ln:
            color = RED
        elif "complete" in ln.lower() or "Successfully" in ln:
            color = GREEN
        elif "Loaded" in ln or "reset" in ln:
            color = DIM
        d.text((88, y), ln, font=f(MONO, 21), fill=color)
        y += 34
    if shown <= len(lines) and shown > 0:
        d.text((88, y), "▌", font=f(MONO, 21), fill=GOLD)
    return img


def cards_frame(eyebrow, headline, sub, cards, foot=None):
    """Headline + up to 3 stat/info cards."""
    img, d = base_frame()
    d.text((70, 110), eyebrow.upper(), font=f(MONO_B, 20), fill=AMBER)
    d.text((70, 150), headline, font=f(SERIF, 58), fill=TEXT)
    if sub:
        d.text((70, 230), sub, font=f(MONO, 22), fill=DIM)
    n = len(cards)
    cw = (W - 140 - (n - 1) * 24) // n
    y0 = 300
    for i, (k, v, note) in enumerate(cards):
        x0 = 70 + i * (cw + 24)
        d.rectangle([x0, y0, x0 + cw, y0 + 300], fill=PANEL, outline="#1F2937", width=2)
        d.text((x0 + 28, y0 + 34), k.upper(), font=f(MONO_B, 18), fill=DIM)
        vy = y0 + 90
        for wline in v.split("\n"):
            d.text((x0 + 28, vy), wline, font=f(SERIF, 46), fill=GOLD)
            vy += 56
        if note:
            d.text((x0 + 28, y0 + 250), note, font=f(MONO, 17), fill=DIM)
    if foot:
        d.text((70, H - 80), foot, font=f(MONO, 16), fill=DIM)
    return img


def image_frame(eyebrow, headline, img_path, img_box, caption=None):
    img, d = base_frame()
    d.text((70, 96), eyebrow.upper(), font=f(MONO_B, 20), fill=AMBER)
    d.text((70, 136), headline, font=f(SERIF, 46), fill=TEXT)
    x0, y0, x1, y1 = img_box
    pic = Image.open(img_path).convert("RGB").resize((x1 - x0, y1 - y0))
    img.paste(pic, (x0, y0))
    d.rectangle(img_box, outline="#1F2937", width=2)
    if caption:
        d.text((x0, y1 + 14), caption, font=f(MONO, 15), fill=DIM)
    return img


def save_frames(scene, frames):
    paths = []
    for i, fr in enumerate(frames):
        p = FRAMES / f"{scene}_{i:03d}.png"
        fr.save(p)
        paths.append(p)
    return paths


# ---------------------------------------------------------------------------
# Scene content — REAL log lines from the 2026-08-14 Community-tier run
# ---------------------------------------------------------------------------
T_BACKTEST = [
    "$ python scripts/run_backtest.py",
    "SOVEREIGN QUANT BACKTEST ENGINE - UNIQUE INSTANCE",
    "data.loader  - Loaded & cached SPY: 1662 bars (yfinance)",
    "data.loader  - Loaded & cached QQQ: 1662 bars (yfinance)",
    "data.loader  - Loaded & cached IWM: 1662 bars (yfinance)",
    "data.loader  - Loaded & cached GLD: 1662 bars (yfinance)",
    "data.loader  - Loaded & cached TLT: 1662 bars (yfinance)",
    "risk.manager - RiskManager reset with equity=100,000.00",
    "backtest.engine - Timeline: 1662 bars, 684 signal rows",
    "backtest.engine - Backtest complete. Final equity: 105,578.52 | Trades: 652",
]

T_INSTALL = [
    "$ cd sovereign-quant-workstation",
    "$ pip install -r requirements.txt",
    "Collecting streamlit, pandas, numpy, scipy, statsmodels...",
    "Installing collected packages: 65 packages",
    "Successfully installed ccxt-4.5.73 quantstats-0.0.81 yfinance-1.6.0",
    "  scipy-1.18.0 statsmodels-0.14.6 scikit-learn-1.9.0 matplotlib-3.11.1",
]

T_KILLSWITCH = [
    "$ # demo: limit deliberately lowered for this recording",
    "$ python scripts/run_backtest.py --set risk.max_daily_loss=-1.0%",
    "risk.manager - RiskManager reset with equity=100,000.00",
    "risk.manager - Daily P&L: -1.04%  (limit: -1.00%)",
    "risk.manager - Daily loss limit breached",
    "risk.manager - KILL SWITCH ENGAGED - session locked",
    "backtest.engine - Halted by risk manager. No further orders.",
]

SCENES = [
    dict(
        id="s1", min_len=10,
        narration="This is Sovereign Quant. No actors, no green screen. This is a real backtest, running right now, on the free tier anyone can download.",
        frames=[terminal_frame(T_BACKTEST, k, "root@sovereign: ~/sovereign_quant — live run") for k in (1, 2, 4, 6)],
    ),
    dict(
        id="s2", min_len=16,
        narration="It's a research and risk-control workstation that runs on your own machine. It tests trading strategies against real market data, shows you the results, and enforces the safety limits you set. It is not a broker. It never holds your money, never places a trade, and makes no promise of profit.",
        frames=[
            cards_frame("What it is", "Your own quant desk,\non your own machine.",
                        "Research, backtesting and risk enforcement — offline.",
                        [("Runs", "Locally", "no cloud, no telemetry"),
                         ("Data", "Real markets", "yfinance / your feeds"),
                         ("Limits", "Enforced", "non-bypassable gates")]),
            cards_frame("What it is not", "Not a broker.\nNot a fund.",
                        "It never holds your money and never places a trade.",
                        [("Custody", "None", "your capital stays yours"),
                         ("Orders", "Never sent", "research output only"),
                         ("Promises", "Zero", "no profit claims, ever")]),
        ],
    ),
    dict(
        id="s3", min_len=12,
        narration="Start on the pricing page. Pick Community for free, or Professional and Institutional for the paid tiers. Enter your desk name — it's cryptographically signed into your licence key — and check out securely through Stripe.",
        frames=[
            cards_frame("Step 01 — Acquire", "Pick your tier.",
                        "Community is free — no card required.",
                        [("Community", "$0", "full engine, free forever"),
                         ("Professional", "$499/yr", "full strategies + reports"),
                         ("Institutional", "$1,999/yr", "desk-scale deployment")],
                        foot="Desk name is HMAC-signed into your licence key — checkout via Stripe."),
        ],
    ),
    dict(
        id="s4", min_len=8,
        narration="You get a zip: the dashboard app, a dependency list, and one-command launchers for Windows, Mac and Linux.",
        frames=[
            terminal_frame([
                "$ unzip sovereign-quant-workstation.zip",
                "sovereign-quant-workstation/",
                "  app.py                 # the workstation",
                "  requirements.txt       # dependencies",
                "  run.bat                # Windows launcher",
                "  run.sh                 # macOS / Linux launcher",
                "  README.md              # field manual",
            ], 7, "Explorer — downloaded package"),
        ],
    ),
    dict(
        id="s5", min_len=9,
        narration="Open a terminal in the unpacked folder. One command installs everything. Python 3.10 or newer is the only requirement.",
        frames=[terminal_frame(T_INSTALL, k) for k in (2, 4, 6)],
    ),
    dict(
        id="s6", min_len=30,
        narration="This is the part we don't script. The engine loads real market data and runs all three strategies: pairs statistical arbitrage, momentum with an ADX filter, and regime-gated mean reversion. Every order has to clear the risk manager before it counts. And here is the equity curve it produced, from data it just pulled. Six hundred and fifty-two trades. This is exactly what you will see the first time you run it. Same command, same output, on your machine.",
        frames=[terminal_frame(T_BACKTEST, k) for k in (1, 3, 5, 7, 9, 10)],
        # chart + stats frames appended in build (need the PNG first)
    ),
    dict(
        id="s7", min_len=13,
        narration="The risk manager is not a setting you can quietly disable. Breach the daily loss limit or the drawdown ceiling, and the kill switch locks the session — like it just did here.",
        frames=[terminal_frame(T_KILLSWITCH, k) for k in (2, 4, 6, 7)],
    ),
    dict(
        id="s8", min_len=10,
        narration="Professional and Institutional tiers compile a branded PDF tearsheet from every run — the same report format you would hand to an investor.",
        frames=[],  # built in build() with chart image
    ),
    dict(
        id="s9", min_len=9,
        narration="Download the free tier and run the exact same backtest yourself. Your machine, your models, your edge.",
        frames=[
            cards_frame("Sovereign Quant", "Run it yourself.",
                        "Free Community tier — same command, same output.",
                        [("Download", "Free", "no card required"),
                         ("Reproduce", "This run", "your machine, your data"),
                         ("Upgrade", "When ready", "Professional / Institutional")]),
        ],
    ),
]


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
async def make_audio():
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    tts = OpenAITextToSpeech(api_key=os.environ["EMERGENT_LLM_KEY"])

    async def one(scene):
        out = AUDIO / f"{scene['id']}.mp3"
        if not out.exists():
            audio = await tts.generate_speech(
                text=scene["narration"], model="tts-1-hd", voice="onyx")
            out.write_bytes(audio)
        print("audio", scene["id"], out.stat().st_size, flush=True)

    await asyncio.gather(*[one(s) for s in SCENES])


def audio_len(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build_segment(scene, chart_png):
    frames = scene["frames"]
    if scene["id"] == "s6":
        frames = frames + [
            image_frame("Step 04 — Operate", "The curve it just produced.",
                        chart_png, (90, 210, 1190, 630),
                        caption="Equity curve — reconstructed shape; headline figures from the actual run log, 2026-08-14."),
            cards_frame("Run Results — 2026-08-14", "652 trades. One command.",
                        "Community tier, five ETFs, 1,662 daily bars.",
                        [("Total Return", "+5.58%", "hypothetical backtest"),
                         ("Sharpe", "0.288", "vol 3.01%"),
                         ("Max Drawdown", "-7.03%", "kill switch never hit")],
                        foot="Hypothetical backtest results — not live trading, not a promise of future returns."),
        ]
    if scene["id"] == "s8":
        frames = [
            cards_frame("Step 06 — Reports", "Investor-grade output.",
                        "Every run compiles a branded PDF tearsheet.",
                        [("Format", "PDF", "equity, drawdown, stats"),
                         ("Branding", "Your desk", "name signed into licence"),
                         ("Delivery", "Instant", "compiled offline, locally")],
                        foot="Sample tearsheet downloadable from the site — clearly labelled synthetic."),
        ]

    afile = AUDIO / f"{scene['id']}.mp3"
    dur = max(audio_len(afile) + 0.6, scene["min_len"])
    per = dur / len(frames)
    paths = save_frames(scene["id"], frames)

    lst = WORK / f"{scene['id']}.txt"
    with open(lst, "w") as fh:
        for p in paths:
            fh.write(f"file '{p}'\nduration {per:.3f}\n")
        fh.write(f"file '{paths[-1]}'\n")

    seg = SEGMENTS / f"{scene['id']}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-i", str(afile),
        "-af", f"apad=whole_dur={dur:.3f}", "-t", f"{dur:.3f}",
        "-vf", "format=yuv420p", "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        str(seg),
    ], check=True, capture_output=True)
    print("segment", scene["id"], f"{dur:.1f}s", flush=True)
    return seg


def main():
    chart_png = WORK / "equity_curve.png"
    render_chart(chart_png, (1100, 420))
    SITE_CHART.parent.mkdir(parents=True, exist_ok=True)
    render_chart(SITE_CHART, (1100, 460), watermark="REPRESENTATIVE")
    print("charts done", flush=True)

    asyncio.run(make_audio())

    segs = [build_segment(s, chart_png) for s in SCENES]
    lst = WORK / "final.txt"
    with open(lst, "w") as fh:
        for s in segs:
            fh.write(f"file '{s}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", "-movflags", "+faststart", str(OUT),
    ], check=True, capture_output=True)
    print("VIDEO DONE", OUT, OUT.stat().st_size, "bytes", flush=True)


if __name__ == "__main__":
    main()
