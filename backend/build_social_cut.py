"""Vertical social cut (1080x1920, ~31s) for Facebook / X / TikTok.
Beats: hook -> real terminal replay -> equity curve -> stats -> positioning -> CTA.
Output: /app/frontend/public/proof/sq-social-cut-9x16.mp4 (publicly downloadable).
"""
import asyncio
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from build_how_it_works_video import equity_series, render_chart

load_dotenv("/app/backend/.env")

WORK = Path("/app/backend/social_build")
FRAMES, AUDIO, SEGS = WORK / "frames", WORK / "audio", WORK / "segments"
for d in (FRAMES, AUDIO, SEGS):
    d.mkdir(parents=True, exist_ok=True)

OUT = Path("/app/frontend/public/proof/sq-social-cut-9x16.mp4")
LOGO = Path("/app/frontend/public/sq-logo.png")
CHART = WORK / "chart_vertical.png"

W, H = 1080, 1920
BG, PANEL, GOLD, AMBER = "#0B0F14", "#111827", "#C9A227", "#F59E0B"
TEXT, DIM, GREEN, RED = "#E5E7EB", "#8B93A1", "#10B981", "#EF4444"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
MONO_B = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"


def f(p, s):
    return ImageFont.truetype(p, s)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, W - 24, H - 24], outline="#1F2937", width=3)
    d.text((60, 56), "SOVEREIGN QUANT", font=f(MONO_B, 30), fill=GOLD)
    return img, d


def wrap(d, text, font, width):
    lines, line = [], ""
    for w in text.split():
        t = f"{line} {w}".strip()
        if d.textlength(t, font=font) <= width:
            line = t
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines


def hook_frame():
    img, d = base()
    d.text((60, 420), "THIS IS A REAL BACKTEST.", font=f(SERIF, 74), fill=TEXT)
    d.text((60, 520), "Replaying exactly as it ran.", font=f(SERIF, 54), fill=GOLD)
    for i, ln in enumerate(wrap(d, "No actors. No stock photos. Free tier, one command, your machine.",
                                 f(MONO, 34), W - 160)):
        d.text((60, 660 + i * 50), ln, font=f(MONO, 34), fill=DIM)
    d.rectangle([60, 900, W - 60, 1150], fill="#05070B", outline="#1F2937", width=2)
    d.text((90, 950), "$ python scripts/run_backtest.py", font=f(MONO_B, 32), fill=GOLD)
    d.text((90, 1010), "SOVEREIGN QUANT BACKTEST ENGINE", font=f(MONO, 30), fill=TEXT)
    d.text((90, 1070), "▌", font=f(MONO, 34), fill=GOLD)
    return img


T_LINES = [
    ("$ python scripts/run_backtest.py", GOLD),
    ("data.loader - SPY: 1662 bars (yfinance)", DIM),
    ("data.loader - QQQ: 1662 bars (yfinance)", DIM),
    ("data.loader - IWM: 1662 bars (yfinance)", DIM),
    ("data.loader - GLD: 1662 bars (yfinance)", DIM),
    ("data.loader - TLT: 1662 bars (yfinance)", DIM),
    ("risk.manager - equity=100,000.00", DIM),
    ("engine - 1662 bars, 684 signal rows", DIM),
    ("engine - Final equity: 105,578.52", GREEN),
    ("engine - Trades: 652", GREEN),
]


def terminal_frame(shown):
    img, d = base()
    d.text((60, 330), "REAL DATA. REAL RUN.", font=f(SERIF, 60), fill=TEXT)
    d.rectangle([60, 450, W - 60, 1500], fill="#05070B", outline="#1F2937", width=2)
    for i, c in enumerate((RED, AMBER, GREEN)):
        d.ellipse([92 + i * 36, 482, 110 + i * 36, 500], fill=c)
    y = 540
    for ln, col in T_LINES[:shown]:
        d.text((92, y), ln, font=f(MONO, 28), fill=col)
        y += 52
    d.text((92, y), "▌", font=f(MONO, 30), fill=GOLD)
    return img


def curve_frame():
    img, d = base()
    d.text((60, 300), "THE CURVE IT PRODUCED.", font=f(SERIF, 58), fill=TEXT)
    pic = Image.open(CHART).convert("RGB")
    img.paste(pic, (60, 420))
    d.rectangle([60, 420, 60 + pic.width, 420 + pic.height], outline="#1F2937", width=2)
    d.text((60, 1000), "652 trades. One command.", font=f(SERIF, 52), fill=GOLD)
    for i, ln in enumerate(wrap(d, "Reconstructed shape — headline figures from the actual run log, 14 Aug 2026.",
                                 f(MONO, 26), W - 160)):
        d.text((60, 1100 + i * 40), ln, font=f(MONO, 26), fill=DIM)
    return img


def stats_frame():
    img, d = base()
    d.text((60, 280), "THE NUMBERS.", font=f(SERIF, 64), fill=TEXT)
    rows = [("TOTAL RETURN", "+5.58%", GOLD), ("SHARPE", "0.288", TEXT),
            ("MAX DRAWDOWN", "-7.03%", TEXT), ("TRADES", "652", GOLD)]
    y = 420
    for k, v, col in rows:
        d.rectangle([60, y, W - 60, y + 230], fill=PANEL, outline="#1F2937", width=2)
        d.text((100, y + 40), k, font=f(MONO_B, 30), fill=DIM)
        d.text((100, y + 100), v, font=f(SERIF, 86), fill=col)
        y += 262
    for i, ln in enumerate(wrap(d, "Hypothetical backtest — not live trading, not a promise of future returns.",
                                 f(MONO, 24), W - 160)):
        d.text((60, y + 30 + i * 36), ln, font=f(MONO, 24), fill=DIM)
    return img


def positioning_frame():
    img, d = base()
    d.text((60, 380), "YOUR MACHINE.", font=f(SERIF, 68), fill=TEXT)
    d.text((60, 470), "YOUR MODELS.", font=f(SERIF, 68), fill=TEXT)
    d.text((60, 560), "YOUR EDGE.", font=f(SERIF, 68), fill=GOLD)
    items = ["Runs fully offline — no cloud", "Not a broker — never holds money",
             "Risk gates you can't bypass", "Kill switch locks on breach"]
    y = 760
    for it in items:
        d.text((60, y), "+", font=f(MONO_B, 40), fill=GREEN)
        d.text((120, y), it, font=f(MONO, 36), fill=TEXT)
        y += 80
    return img


def cta_frame():
    img, d = base()
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((220, 220))
        img.paste(logo, (W // 2 - logo.width // 2, 380), logo)
    t = "sovereignquant.com.au"
    ft = f(SERIF, 64)
    tw = d.textlength(t, font=ft)
    d.text((W // 2 - tw // 2, 700), t, font=ft, fill=GOLD)
    lines = ["Download the free tier.", "Run the exact same backtest", "on your own machine."]
    y = 830
    for ln in lines:
        fl = f(SERIF, 46)
        d.text((W // 2 - d.textlength(ln, font=fl) // 2, y), ln, font=fl, fill=TEXT)
        y += 70
    tag = "NO CARD REQUIRED"
    d.text((W // 2 - d.textlength(tag, font=f(MONO_B, 30)) // 2, y + 60), tag,
           font=f(MONO_B, 30), fill=AMBER)
    return img


render_chart(CHART, (960, 540))

BEATS = [
    dict(id="b1", min_len=4.0, frames=[hook_frame()],
         narration="This is a real backtest, replaying exactly as it ran."),
    dict(id="b2", min_len=6.0,
         frames=[terminal_frame(k) for k in (1, 3, 5, 7, 9, 10)],
         narration="Sovereign Quant loads real market data, runs three strategies, and every order has to clear the risk manager."),
    dict(id="b3", min_len=6.0, frames=[curve_frame()],
         narration="Here is the equity curve, rebuilt from the actual run log. Six hundred and fifty-two trades. One command."),
    dict(id="b4", min_len=5.5, frames=[stats_frame()],
         narration="Plus five point five eight percent. Sharpe zero point two eight eight. Max drawdown, minus seven percent."),
    dict(id="b5", min_len=5.0, frames=[positioning_frame()],
         narration="It runs entirely on your machine. No cloud, no custody, no profit promises."),
    dict(id="b6", min_len=5.5, frames=[cta_frame()],
         narration="Download the free tier at sovereign quant dot com dot A U — and run the exact same backtest yourself."),
]


async def make_audio():
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    tts = OpenAITextToSpeech(api_key=os.environ["EMERGENT_LLM_KEY"])

    async def one(b):
        out = AUDIO / f"{b['id']}.mp3"
        if not out.exists():
            audio = await tts.generate_speech(text=b["narration"], model="tts-1-hd", voice="onyx")
            out.write_bytes(audio)
        print("audio", b["id"], out.stat().st_size, flush=True)

    await asyncio.gather(*[one(b) for b in BEATS])


def audio_len(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    render_chart(CHART, (960, 540))
    asyncio.run(make_audio())

    segs = []
    for b in BEATS:
        afile = AUDIO / f"{b['id']}.mp3"
        dur = max(audio_len(afile) + 0.5, b["min_len"])
        per = dur / len(b["frames"])
        paths = []
        for i, fr in enumerate(b["frames"]):
            p = FRAMES / f"{b['id']}_{i:02d}.png"
            fr.save(p)
            paths.append(p)
        lst = WORK / f"{b['id']}.txt"
        with open(lst, "w") as fh:
            for p in paths:
                fh.write(f"file '{p}'\nduration {per:.3f}\n")
            fh.write(f"file '{paths[-1]}'\n")
        seg = SEGS / f"{b['id']}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-i", str(afile), "-af", f"apad=whole_dur={dur:.3f}", "-t", f"{dur:.3f}",
            "-vf", "format=yuv420p", "-r", "30",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", str(seg),
        ], check=True, capture_output=True)
        print("segment", b["id"], f"{dur:.1f}s", flush=True)
        segs.append(seg)

    lst = WORK / "final.txt"
    with open(lst, "w") as fh:
        for s in segs:
            fh.write(f"file '{s}'\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", "-movflags", "+faststart", str(OUT)],
                   check=True, capture_output=True)
    print("SOCIAL CUT DONE", OUT, OUT.stat().st_size, "bytes", flush=True)


if __name__ == "__main__":
    main()
