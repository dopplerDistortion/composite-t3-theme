"""Render one frame of the DitherWave shader as a palette PNG in the goksen.ing grey ladder.

A pure-Python port of the Framer DitherWave fragment shader (no mouse influence).
Usage: python3 -I dither_render.py OUT.png [css_w css_h time levels scale]
"""
import math
import struct
import sys
import zlib

out = sys.argv[1]
CSS_W = int(sys.argv[2]) if len(sys.argv) > 2 else 2560
CSS_H = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
TIME = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
LEVELS = int(sys.argv[5]) if len(sys.argv) > 5 else 5
SCALE = int(sys.argv[6]) if len(sys.argv) > 6 else 2  # device pixels per CSS pixel

PIXEL = 7  # css px per dither cell, as the component default
SPEED = 6.6 / 100
FREQ = max(1.1, 0.2)
AMP = 30 / 100

# Ink, Card, Well, Rule, Mark: level 0 is the page ground.
PALETTE = (sys.argv[7].split(",") if len(sys.argv) > 7 else ["0b0b0c", "131314", "1c1c1d", "2a2a2b", "5c5b58"])[:LEVELS]

BAYER = [
    [0, 48, 12, 60, 3, 51, 15, 63],
    [32, 16, 44, 28, 35, 19, 47, 31],
    [8, 56, 4, 52, 11, 59, 7, 55],
    [40, 24, 36, 20, 43, 27, 39, 23],
    [2, 50, 14, 62, 1, 49, 13, 61],
    [34, 18, 46, 30, 33, 17, 45, 29],
    [10, 58, 6, 54, 9, 57, 5, 53],
    [42, 26, 38, 22, 41, 25, 37, 21],
]


def mod289(x):
    return x - math.floor(x * (1.0 / 289.0)) * 289.0


def permute(x):
    return mod289(((x * 34.0) + 1.0) * x)


def fract(x):
    return x - math.floor(x)


def cnoise(px, py):
    ix0, iy0 = math.floor(px), math.floor(py)
    fx0, fy0 = px - ix0, py - iy0
    ix0, iy0, ix1, iy1 = mod289(ix0), mod289(iy0), mod289(ix0 + 1.0), mod289(iy0 + 1.0)
    fx1, fy1 = fx0 - 1.0, fy0 - 1.0
    # corner order matches the shader: (x0,y0) (x1,y0) (x0,y1) (x1,y1)
    corners = ((ix0, iy0, fx0, fy0), (ix1, iy0, fx1, fy0), (ix0, iy1, fx0, fy1), (ix1, iy1, fx1, fy1))
    n = []
    for cx, cy, dx, dy in corners:
        i = permute(permute(cx) + cy)
        gx = fract(i * (1.0 / 41.0)) * 2.0 - 1.0
        gy = abs(gx) - 0.5
        gx -= math.floor(gx + 0.5)
        norm = 1.79284291400159 - 0.85373472095314 * (gx * gx + gy * gy)
        n.append((gx * norm) * dx + (gy * norm) * dy)
    ux = fx0 * fx0 * fx0 * (fx0 * (fx0 * 6.0 - 15.0) + 10.0)
    uy = fy0 * fy0 * fy0 * (fy0 * (fy0 * 6.0 - 15.0) + 10.0)
    a = n[0] + (n[1] - n[0]) * ux
    b = n[2] + (n[3] - n[2]) * ux
    return 2.3 * (a + (b - a) * uy)


def fbm(px, py):
    value, amp = 0.0, 1.0
    for _ in range(8):
        value += amp * abs(cnoise(px, py))
        px *= FREQ
        py *= FREQ
        amp *= AMP
    return value


cols = math.ceil(CSS_W / PIXEL)
rows = math.ceil(CSS_H / PIXEL)
aspect = CSS_W / CSS_H
grid = []
counts = [0] * LEVELS
for cy in range(rows):
    row = []
    for cx in range(cols):
        u = (cx + 0.5) * PIXEL / CSS_W
        v = (cy + 0.5) * PIXEL / CSS_H
        px, py = (u - 0.5) * aspect, v - 0.5
        p2x, p2y = px - TIME * SPEED, py - TIME * SPEED
        inner = fbm(p2x, p2y)
        mid = fbm(px + inner, py + inner)
        f = fbm(px - mid, py - mid)
        f = min(max(f, 0.0), 1.0)
        val = f + (BAYER[cy % 8][cx % 8] / 64.0 - 0.25) / (LEVELS - 1)
        val = min(max(val - 0.2, 0.0), 1.0)
        level = int(math.floor(val * (LEVELS - 1) + 0.5))
        counts[level] += 1
        row.append(level)
    grid.append(row)

grid.reverse()  # gl_FragCoord grows upward; PNG rows grow downward

cell = PIXEL * SCALE
width, height = CSS_W * SCALE, CSS_H * SCALE
raw = bytearray()
for y in range(height):
    src = grid[min(y // cell, rows - 1)]
    raw.append(0)
    raw.extend(src[min(x // cell, cols - 1)] for x in range(width))


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


plte = b"".join(bytes.fromhex(h) for h in PALETTE)
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0))
png += chunk(b"PLTE", plte)
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")
open(out, "wb").write(png)
total = sum(counts)
print(f"{width}x{height}px, {cols}x{rows} cells, {len(png)} bytes")
print("level share:", {PALETTE[i]: f"{counts[i] / total:.1%}" for i in range(LEVELS)})
