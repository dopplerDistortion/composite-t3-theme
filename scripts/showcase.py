"""Compose docs/showcase.png, a bento of detail crops, from full-window captures.

Usage: python3 scripts/showcase.py CAPTURES_DIR

CAPTURES_DIR holds s1.png .. s6.png: 1112x997 captures of T3 Code at 1x with the
Composite theme on (thread view, draft in the composer, model picker, Settings >
General, Settings > Providers, a thread while it works). Redact them before you
run this; the script only crops. Needs Pillow and Google Chrome.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = ROOT / "docs/showcase.png"
RULE = (42, 42, 43)

# (capture, box x0 y0 x1 y1, label, right text). Box width sets the column.
COLUMNS = [
    [
        ("s1", (0, 90, 256, 192), "Selected row", "bone"),
        ("s6", (0, 766, 256, 950), "Busy", "amber"),
        ("s4", (40, 41, 296, 661), "Settings nav", "icons"),
    ],
    [
        ("s1", (304, 52, 1064, 500), "Markdown table", "Geist Mono"),
        ("s2", (304, 226, 1064, 522), "Code", "weight, not colour"),
        ("s2", (304, 535, 1064, 790), "Blockquote", "rule"),
        ("s6", (304, 760, 1064, 990), "Working", "stop is red"),
    ],
    [
        ("s3", (300, 520, 1060, 933), "Popover", "crop marks"),
        ("s5", (300, 170, 1060, 405), "Providers", "own glyphs"),
        ("s4", (300, 110, 1060, 560), "Settings groups", "panels"),
        ("s2", (300, 852, 1060, 990), "Send", "the one red"),
    ],
]

SWATCHES = [
    ("Ink", "#0b0b0c"), ("Card", "#131314"), ("Well", "#1c1c1d"), ("Rule", "#2a2a2b"),
    ("Mark", "#5c5b58"), ("Muted", "#8c8a86"), ("Bone", "#e6e3de"),
    ("Signal", "#ff3b30"), ("Warn", "#f5b400"),
]

CSS = """
*{box-sizing:border-box;margin:0}
body{background:#0b0b0c url(bg.png) center/cover;color:#e6e3de;font:400 14px/1.4 "Geist Mono",ui-monospace,monospace;padding:48px 45px;width:1920px}
.grid{display:flex;gap:24px;align-items:flex-start}
.col{display:flex;flex-direction:column;gap:32px}
.panel{position:relative;background:#131314;border:1px solid #2a2a2b}
.panel::before,.panel::after{content:"";position:absolute;width:10px;height:10px;border:0 solid #5c5b58}
.panel::before{top:-7px;left:-7px;border-top-width:1px;border-left-width:1px}
.panel::after{bottom:-7px;right:-7px;border-bottom-width:1px;border-right-width:1px}
.label{display:flex;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #2a2a2b;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8c8a86}
.label b{font-weight:400;color:#e6e3de}
.panel img{display:block}
.title{padding:20px 16px 24px}
.title h1{font:300 32px/.92 "Martian Mono",ui-monospace,monospace;font-stretch:112.5%;letter-spacing:-.01em}
.title p{margin-top:16px;color:#8c8a86;font-size:12px}
.sw{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid #2a2a2b}
.sw div{padding:10px 12px 12px;border-right:1px solid #2a2a2b;border-bottom:1px solid #2a2a2b;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8c8a86}
.sw div:nth-child(3n){border-right:0}
.sw div:nth-last-child(-n+3){border-bottom:0}
.sw i{display:block;height:28px;margin-bottom:8px;border:1px solid #2a2a2b}
"""


def main():
    caps = Path(sys.argv[1])
    work = Path(tempfile.mkdtemp(prefix="showcase-"))
    shutil.copy(ROOT / "dist/composite.png", work / "bg.png")
    cols, n = [], 0
    for c, column in enumerate(COLUMNS):
        tiles = []
        if c == 0:
            sw = "".join(f'<div><i style="background:{h}"></i>{name}</div>' for name, h in SWATCHES)
            tiles.append(
                '<section class=panel><div class=label><span>00 · Theme</span><b>T3 Code</b></div>'
                '<div class=title><h1>Composite</h1><p>Two inks, one signal. Square, flat, monospace.</p></div>'
                f'<div class=sw>{sw}</div></section>'
            )
        for cap, box, label, right in column:
            n += 1
            name = f"t{n:02}.png"
            Image.open(caps / f"{cap}.png").convert("RGB").crop(box).save(work / name)
            tiles.append(
                f'<section class=panel><div class=label><span>{n:02} · {label}</span><b>{right}</b></div>'
                f'<img src={name} width={box[2] - box[0]} height={box[3] - box[1]}></section>'
            )
        width = column[0][1][2] - column[0][1][0] + 2  # the image plus the 1px frame
        cols.append(f"<div class=col style=width:{width}px>{''.join(tiles)}</div>")
    page = work / "index.html"
    page.write_text(f"<!doctype html><meta charset=utf-8><style>{CSS}</style><div class=grid>{''.join(cols)}</div>")
    raw = work / "raw.png"
    subprocess.run(
        [CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
         "--window-size=1920,2400", f"--screenshot={raw}", page.as_uri()],
        check=True, capture_output=True,
    )
    # Trim the ground under the tallest column and keep a 48px margin. The dither
    # ground is not flat Ink, so look for the last row a Panel frame (Rule) touches.
    img = Image.open(raw).convert("RGB")
    px = img.load()
    bottom = next(y for y in range(img.height - 1, 0, -1)
                  if any(px[x, y] == RULE for x in range(48, img.width - 48, 2)))
    img.crop((0, 0, img.width, bottom + 1 + 48)).save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)} {img.width}x{bottom + 49}")


main()
