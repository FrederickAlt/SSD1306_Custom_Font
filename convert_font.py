#!/usr/bin/env python3
#
# Author: Frederick Altrock frederick.altrock@web.de
# License: cc-by 4.0
# Created: 2025-09-09
#

"""
Convert a TTF font into the custom .pf format used by SSD1306 driver.
Requires Pillow: pip install pillow
"""



import os
import sys
from pathlib import Path
try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("Requires Pillow. Run: pip install pillow.")

# Default search paths for fonts
SYSTEM_FONT_DIRS = [
    "/usr/share/fonts", # Linux OS fonts
    "/usr/local/share/fonts", # Linux OS fonts
    str(Path.home() / ".fonts"), # Linux user fonts
    str(Path.home() / "Fonts"),  # Mac user fonts
    "C:/Windows/Fonts", # Windows OS Fonts
    "/System/Library/Fonts", # Mac OS Fonts
    "/Library/Fonts", # Mac OS Fonts
]


def find_ttf(fontname: str) -> str:
    """
    Look for a TTF file in this order:
    1. Check if fontname is a valid path.
    2. Check CWD.
    3. Search system font directories recursively.
    """
    path = Path(fontname)
    # 1. If fontname is an existing file
    if path.exists() and path.suffix.lower() == ".ttf":
        return str(path)

    # 2. Check CWD
    candidate = Path(os.getcwd()) / f"{fontname}.ttf"
    if candidate.exists():
        return str(candidate)

    # 3. Search system font directories
    for d in SYSTEM_FONT_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        for f in base.rglob("*.ttf"):
            if f.stem.lower() == fontname.lower():
                return str(f)

    raise FileNotFoundError(
        f"Could not find {fontname}.ttf as a path, in CWD, or system font directories."
    )


def ttf_to_pf(fontname: str, size: int = 12, charset=None, out_file=None):
    """
    Convert TTF into .pf format.
    """
    ttf_path = find_ttf(fontname)
    print(f"Using font: {ttf_path}")

    if charset is None:
        # Printable ASCII
        charset = [chr(i) for i in range(32, 127)]

    if out_file is None:
        out_file = f"{Path(fontname).stem}{size}.pf"

    font = ImageFont.truetype(ttf_path, size)

    # Header: PF + default char '?' + number of characters
    default_char = ord("?")
    header = bytearray([ord("P"), ord("F"), default_char, len(charset)])

    char_table = bytearray()
    bitmaps = bytearray()

    ascent, descent = font.getmetrics()
    line_height = ascent + descent  # total vertical space per line

    for char in charset:
        x0, y0, x1, y1 = font.getbbox(char)
        w, h = x1 - x0, y1 - y0

        # Create image for this glyph
        img = Image.new("L", (w, line_height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((-x0, 0), char, font=font, fill=1)
        start_index = len(bitmaps)

        # Pack row-wise bits
        for y in range(line_height):
            byte = 0
            bit_count = 0
            for x in range(w):
                pixel = img.getpixel((x, y))
                byte = (byte << 1) | (1 if pixel else 0)
                bit_count += 1
                if bit_count == 8:
                    bitmaps.append(byte)
                    byte, bit_count = 0, 0
            if bit_count > 0:
                bitmaps.append(byte << (8 - bit_count))

        # Char table entry
        char_table.extend([
            ord(char),
            w,
            line_height,
            start_index & 0xFF,
            (start_index >> 8) & 0xFF,
        ])

    with open(out_file, "wb") as f:
        f.write(header)
        f.write(char_table)
        f.write(bitmaps)

    print(f"Font written to {out_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_font.py FONTNAME [height]")
        sys.exit(1)

    fontname = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    ttf_to_pf(fontname, size)
