#!/usr/bin/env python3
#
# Author: Frederick Altrock frederick.altrock@web.de
# License: cc-by 4.0
# Created: 2025-09-09
#

"""
List available TTF fonts (basenames only).
Searches using the following priority:
1. If argument is a path, check if it exists.
2. Current working directory.
3. System font directories recursively.
"""

from pathlib import Path

# System font directories
SYSTEM_FONT_DIRS = [
    "/usr/share/fonts", # Linux OS fonts
    "/usr/local/share/fonts", # Linux OS fonts
    str(Path.home() / ".fonts"), # Linux user fonts
    str(Path.home() / "Fonts"),  # Mac user fonts
    "C:/Windows/Fonts", # Windows OS Fonts
    "/System/Library/Fonts", # Mac OS Fonts
    "/Library/Fonts", # Mac OS Fonts
]

def list_all_fonts():
    fonts = []

    # 1. Fonts in CWD
    fonts.extend([f.stem for f in Path.cwd().glob("*.ttf")])

    # 2. Fonts in system directories
    for d in SYSTEM_FONT_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        fonts.extend([f.stem for f in base.rglob("*.ttf")])

    # Remove duplicates and sort
    return sorted(set(fonts))


if __name__ == "__main__":
    fonts = list_all_fonts()
    for f in fonts:
        print(f)
