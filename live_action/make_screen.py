"""Clean, photoreal-style iPhone lock screen with the AylluOS notification.

Output: lock_screen_1170x2532.png (screen only, for screen replacement / image-to-video start frame)
"""
import math
import os
import re

import cairo
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "animation", "assets")
W, H = 1170, 2532


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def text(ctx, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_NORMAL, family="Inter", align="left"):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, weight)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    dx = {"left": 0, "center": -e.x_advance / 2, "right": -e.x_advance}[align]
    ctx.move_to(x + dx, y)
    ctx.set_source_rgba(*rgba)
    ctx.show_text(s)


def main():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    # wallpaper: night indigo to dusk lavender (AylluOS palette)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.09, 0.10, 0.25)
    g.add_color_stop_rgb(0.55, 0.22, 0.15, 0.52)
    g.add_color_stop_rgb(1, 0.55, 0.42, 0.80)
    ctx.set_source(g)
    ctx.paint()
    rng = np.random.default_rng(3)
    for _ in range(70):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H * 0.7), rng.uniform(1, 3)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, rng.uniform(0.25, 0.8))
        ctx.fill()
    # lock screen text
    text(ctx, "Saturday, October 31", W / 2, 300, 50, (1, 1, 1, 0.92), cairo.FONT_WEIGHT_BOLD, align="center")
    text(ctx, "8:31", W / 2, 560, 250, (1, 1, 1, 0.96), family="Inter Display", align="center")
    # notification card (frosted)
    cx, cy, cw, chh = 50, 760, W - 100, 760
    rrect(ctx, cx, cy, cw, chh, 54)
    ctx.set_source_rgba(0.97, 0.96, 1.0, 0.86)
    ctx.fill()
    # app icon with woven mark
    ix, iy, isz = cx + 44, cy + 44, 110
    rrect(ctx, ix, iy, isz, isz, 26)
    ctx.set_source_rgb(0.94, 0.93, 1.0)
    ctx.fill()
    svg = open(os.path.join(ASSETS, "aylluos_mark.svg")).read()
    k = isz / 100
    for pts, fill in re.findall(r'<polygon points="([^"]+)" fill="#([0-9A-Fa-f]{6})"', svg):
        p = [tuple(map(float, q.split(","))) for q in pts.split()]
        ctx.move_to(ix + p[0][0] * k, iy + p[0][1] * k)
        for x, y in p[1:]:
            ctx.line_to(ix + x * k, iy + y * k)
        ctx.close_path()
        ctx.set_source_rgb(*[int(fill[i:i + 2], 16) / 255 for i in (0, 2, 4)])
        ctx.fill()
    ctx.move_to(ix + 50 * k, iy + 40.2 * k)
    ctx.curve_to(ix + 54.55 * k, iy + 44.05 * k, ix + 56.65 * k, iy + 49.3 * k, ix + 55.6 * k, iy + 53.85 * k)
    ctx.curve_to(ix + 54.76 * k, iy + 57.42 * k, ix + 52.52 * k, iy + 59.45 * k, ix + 50 * k, iy + 59.45 * k)
    ctx.curve_to(ix + 47.48 * k, iy + 59.45 * k, ix + 45.24 * k, iy + 57.42 * k, ix + 44.4 * k, iy + 53.85 * k)
    ctx.curve_to(ix + 43.35 * k, iy + 49.3 * k, ix + 45.45 * k, iy + 44.05 * k, ix + 50 * k, iy + 40.2 * k)
    ctx.set_source_rgb(0xF4 / 255, 0x77 / 255, 0x21 / 255)
    ctx.fill()
    text(ctx, "AylluOS", ix + isz + 30, iy + 72, 46, (0.15, 0.13, 0.20, 1), cairo.FONT_WEIGHT_BOLD)
    text(ctx, "now", cx + cw - 44, iy + 72, 40, (0.40, 0.38, 0.45, 1), align="right")
    text(ctx, "Baby is Sleeping", cx + 44, cy + 260, 70, (0.07, 0.06, 0.10, 1), cairo.FONT_WEIGHT_BOLD)
    text(ctx, "8:31pm · Grandma", cx + 44, cy + 340, 54, (0.20, 0.18, 0.24, 1))
    surf.flush()
    base = Image.frombuffer("RGBA", (W, H), bytes(surf.get_data()), "raw", "BGRA", 0, 1).convert("RGBA")
    # sleeping-baby image inside the card
    baby = Image.open(os.path.join(ASSETS, "baby_sleeping.webp")).convert("RGBA")
    bw = cw - 88
    bh = 360
    sb = baby.width / bw
    crop = baby.crop((0, int(baby.height * 0.06), baby.width, int(baby.height * 0.06 + bh * sb)))
    crop = crop.resize((bw, bh), Image.LANCZOS)
    bg = Image.new("RGBA", (bw, bh), (0xEF, 0xED, 0xFF, 255))
    bg.alpha_composite(crop)
    crop = bg
    mask = Image.new("L", (bw, bh), 0)
    ms = cairo.ImageSurface(cairo.FORMAT_A8, bw, bh)
    mc = cairo.Context(ms)
    rrect(mc, 0, 0, bw, bh, 30)
    mc.fill()
    ms.flush()
    mask = Image.frombuffer("L", (bw, bh), bytes(ms.get_data()), "raw", "L", ms.get_stride(), 1)
    base.paste(crop, (cx + 44, cy + 375), mask)
    out = os.path.join(HERE, "lock_screen_1170x2532.png")
    base.convert("RGB").save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
