import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BACKEND = Path("/app/backend")
FRAMES = BACKEND / "video_frames"
FRAMES.mkdir(exist_ok=True)

STEPS = [
    ("01", "ACQUIRE YOUR LICENCE"),
    ("02", "DOWNLOAD THE WORKSTATION"),
    ("03", "INSTALL DEPENDENCIES"),
    ("04", "LAUNCH THE ENGINE"),
    ("05", "ACTIVATE OFFLINE"),
    ("06", "OPERATE"),
]

FONT = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

for num, title in STEPS:
    img = Image.new("RGB", (1280, 720), "#050505")
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 1260, 700], outline="#FF3333", width=4)
    d.text((60, 60), "SOVEREIGN//QUANT — FIELD MANUAL", font=ImageFont.truetype(FONT, 28), fill="#8C8C94")
    d.text((60, 220), num, font=ImageFont.truetype(FONT, 220), fill="#FF3333")
    words = title.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) > 22:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    lines.append(line)
    y = 480
    for ln in lines:
        d.text((60, y), ln, font=ImageFont.truetype(FONT, 54), fill="#F5F5F0")
        y += 70
    img.save(FRAMES / f"frame_{num}.png")
    print("frame", num, "done")
