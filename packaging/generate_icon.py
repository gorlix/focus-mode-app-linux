#!/usr/bin/env python3
"""
build/generate_icon.py
Generates the Focus Mode App icon (256x256 PNG) using Pillow.
Matches the purple "M" circle drawn at runtime by PyQt6.
Run: python3 packaging/generate_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def generate_icon(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size // 16
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#6750A4",
    )

    font_size = size // 2
    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "M", font=font)
    x = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), "M", fill="white", font=font)

    return img


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "appimage" / "focus-mode-app.png"
    out.parent.mkdir(exist_ok=True)
    generate_icon(256).save(out, "PNG")
    print(f"Icon written to {out}")
