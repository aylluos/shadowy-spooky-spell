"""Isometric cut-away trattoria: the static painted background (ink + gouache)."""
import math

import numpy as np

from wc import ellipse, spline, rrect

C30, S30 = math.cos(math.pi / 6), 0.5
OX, OY = 540.0, 830.0          # world position of the back floor corner
L = 760.0                      # room size (iso units)
HW = 640.0                     # wall height
WALLT = 26.0                   # wall thickness
SLAB = 56.0


RS = 0.72                      # room scale about the table centre (keeps the whole diorama in frame)
SCALE = [1.0]


def P(x, y, z=0.0):
    k = SCALE[0]
    if k != 1.0:
        x, y, z = 390 + (x - 390) * k, 390 + (y - 390) * k, z * k
    return (OX + (x - y) * C30, OY + (x + y) * S30 - z)


def PA(pts):
    return np.array([P(*p) for p in pts], float)


def circ3(cx, cy, r, z, n=48):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return PA([(cx + r * math.cos(t), cy + r * math.sin(t), z) for t in a])


# iso screen angles (degrees) of the axes
ANG_X = 30.0      # +x axis on screen
ANG_Y = 150.0     # +y axis on screen
INKC = (0.13, 0.09, 0.08)

# ---------------------------------------------------------------- lighting
LAMP_POOL = (540.0, 1095.0)
LAMP_Z = 520.0


def _scaled(x, y, z):
    SCALE[0] = RS
    p = P(x, y, z)
    SCALE[0] = 1.0
    return p


WINC = _scaled(420, 0, 380)
SCONCE = _scaled(0, 600, 430)


def make_light(candle=1.0, phone=0.0, phone_pos=(621, 1136)):
    def f(x, y):
        out = np.empty(np.broadcast(x, y).shape + (3,), np.float32)
        amb = np.array([0.60, 0.52, 0.56], np.float32)
        out[:] = amb
        d = ((x - LAMP_POOL[0]) / 330.0) ** 2 + ((y - LAMP_POOL[1]) / 260.0) ** 2
        g = np.exp(-d * 1.4)
        out += g[..., None] * np.array([0.78, 0.58, 0.34], np.float32) * candle
        d2 = ((x - 540) / 170.0) ** 2 + ((y - 820) / 150.0) ** 2
        out += np.exp(-d2)[..., None] * np.array([0.35, 0.25, 0.12], np.float32)
        # cool window light on the right wall
        d3 = ((x - WINC[0]) / 200.0) ** 2 + ((y - WINC[1]) / 230.0) ** 2
        out += np.exp(-d3)[..., None] * np.array([0.05, 0.10, 0.20], np.float32)
        # sconce on left wall
        d4 = ((x - SCONCE[0]) / 140.0) ** 2 + ((y - SCONCE[1]) / 150.0) ** 2
        out += np.exp(-d4)[..., None] * np.array([0.40, 0.28, 0.14], np.float32)
        if phone > 0:
            d5 = ((x - phone_pos[0]) / 90.0) ** 2 + ((y - phone_pos[1]) / 70.0) ** 2
            out += (phone * np.exp(-d5))[..., None] * np.array([0.25, 0.35, 0.55], np.float32)
        return out
    return f


# ---------------------------------------------------------------- pieces
def quadA(x0, x1, z0, z1, y=0.0):
    return PA([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)])


def quadB(y0, y1, z0, z1, x=0.0):
    return PA([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)])


def box(cv, x0, x1, y0, y1, z0, z1, col, key, top=None, hatch_sides=True, lw=1.4):
    top_p = PA([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
    fy = PA([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)])   # faces +y (screen lower-left)
    fx = PA([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])   # faces +x (screen lower-right)
    c = np.asarray(col)
    cv.gouache(fy, c * 0.78, key=key + "fy", shade=0.2, boil=False)
    cv.gouache(fx, c * 0.62, key=key + "fx", shade=0.2, boil=False)
    cv.gouache(top_p, np.asarray(top if top is not None else c), key=key + "tp", shade=0.12, boil=False)
    if hatch_sides:
        cv.hatch(fx, angle=ANG_Y - 180 + 60, spacing=5, alpha=0.35, key=key + "hx", boil=False)
    cv.ink([(top_p, True, lw), (fy, True, lw), (fx, True, lw)], key=key, boil=False)
    return top_p, fy, fx


def bottle(cv, x, y, z, h, r, col, key):
    """vertical bottle standing at iso position"""
    bx, by = P(x, y, z)
    rx = r * 1.22
    body = np.vstack([ellipse(bx, by, rx, rx * 0.5, n=16, a0=0, a1=math.pi),
                      [(bx - rx, by - h * 0.62), (bx - rx * 0.35, by - h * 0.8), (bx - rx * 0.3, by - h),
                       (bx + rx * 0.3, by - h), (bx + rx * 0.35, by - h * 0.8), (bx + rx, by - h * 0.62)]])
    cv.gouache(body, col, key=key, shade_dir=(1, 0.2), shade=0.45, boil=False)
    cv.pstroke([(bx - rx * 0.5, by - h * 0.55), (bx - rx * 0.55, by - h * 0.1)], 1.6, (1, 0.95, 0.8), 0.6, key=key)
    cv.ink([(body, True, 1.2)], key=key, boil=False)


# ---------------------------------------------------------------- background
def draw_background(cv):
    SCALE[0] = RS
    try:
        _draw_background(cv)
    finally:
        SCALE[0] = 1.0


def _draw_background(cv):
    k = "bg"
    # night void behind the diorama
    sky = rrect(-300, -300, 1400, 2300, 10)
    cv.gouache(sky, (0.16, 0.15, 0.27), color2=(0.22, 0.16, 0.28), key=k + "void", shade_dir=(0, 1), shade=-0.4,
               tex=0.05, light=False, boil=False, jit=0)
    rng = np.random.default_rng(4)
    for j in range(60):
        x, y = rng.uniform(-20, 1100), rng.uniform(0, 1950)
        cv.paint(ellipse(x, y, 1.6, 1.6, n=6), (0.9, 0.88, 0.8), rng.uniform(0.2, 0.6))
    for j in range(5):
        x, y = rng.uniform(0, 1080), rng.uniform(0, 300)
        cv.wash(ellipse(x, y, rng.uniform(120, 220), rng.uniform(25, 45)), (0.42, 0.36, 0.55), dens=0.3, soft=12,
                key=k + f"cl{j}", hard=1.2, boil=False)

    # slab (diorama base)
    sy = PA([(0, L, 0), (L, L, 0), (L, L, -SLAB), (0, L, -SLAB)])
    sx = PA([(L, 0, 0), (L, L, 0), (L, L, -SLAB), (L, 0, -SLAB)])
    cv.gouache(sy, (0.30, 0.19, 0.13), key=k + "sy", shade=0.2, boil=False)
    cv.gouache(sx, (0.24, 0.15, 0.11), key=k + "sx", shade=0.2, boil=False)
    cv.hatch(sy, angle=ANG_X, spacing=4.5, alpha=0.5, key=k + "hsy", boil=False)
    cv.hatch(sx, angle=ANG_Y, spacing=4.5, alpha=0.6, key=k + "hsx", boil=False, cross=90)
    cv.ink([(sy, True, 1.6), (sx, True, 1.6)], key=k + "slab", boil=False)
    # stone line in slab
    cv.ink([(PA([(0, L, -20), (L, L, -20)]), False, 1.0), (PA([(L, 0, -20), (L, L, -20)]), False, 1.0)],
           key=k + "slabl", boil=False, alpha=0.6)

    # ---- walls: wall A (y=0, right back) and wall B (x=0, left back)
    wa = quadA(0, L, 0, HW)
    wb = quadB(0, L, 0, HW)
    cv.gouache(wa, (0.86, 0.62, 0.44), color2=(0.82, 0.52, 0.40), key=k + "wa", shade_dir=(0, -1), shade=0.15,
               tex=0.06, boil=False)
    cv.gouache(wb, (0.76, 0.54, 0.40), color2=(0.70, 0.46, 0.38), key=k + "wb", shade_dir=(0, -1), shade=0.15,
               tex=0.06, boil=False)
    cv.hatch(wa, angle=ANG_X + 60, spacing=6, alpha=0.3, key=k + "wah1", boil=False, fade=((-0.87, -0.5), 0.55, 1.0))
    cv.hatch(wb, angle=ANG_Y - 60, spacing=6, alpha=0.3, key=k + "wbh1", boil=False, fade=((0.87, -0.5), 0.55, 1.0))
    cv.hatch(wb, angle=ANG_X, spacing=7, alpha=0.22, key=k + "wbh2", boil=False, fade=((-1, 0), 0.5, 1.0))
    cv.hatch(wa, angle=ANG_Y, spacing=7, alpha=0.22, key=k + "wah2", boil=False, fade=((1, 0), 0.6, 1.0))
    # weathering stains
    for j in range(9):
        x = rng.uniform(40, L - 60)
        z = rng.uniform(150, HW - 40)
        w2, h2 = rng.uniform(40, 110), rng.uniform(30, 90)
        if j % 2:
            poly = PA([(x - w2, 0, z - h2), (x + w2, 0, z - h2), (x + w2, 0, z + h2), (x - w2, 0, z + h2)])
        else:
            poly = PA([(0, x - w2, z - h2), (0, x + w2, z - h2), (0, x + w2, z + h2), (0, x - w2, z + h2)])
        cv.wash(spline(poly, True, 6), (0.62, 0.42, 0.34), dens=0.25, soft=10, key=k + f"st{j}", hard=1.6,
                boil=False, light=False)
    # exposed bricks (plaster fallen off)
    for (wall, c0, c1, z0, z1) in (("A", 600, 720, 380, 520), ("B", 520, 660, 180, 300), ("A", 40, 140, 470, 560)):
        pts = []
        for t in np.linspace(0, 2 * math.pi, 14, endpoint=False):
            u = (c0 + c1) / 2 + (c1 - c0) / 2 * math.cos(t) * rng.uniform(0.75, 1.05)
            v = (z0 + z1) / 2 + (z1 - z0) / 2 * math.sin(t) * rng.uniform(0.75, 1.05)
            pts.append((u, 0, v) if wall == "A" else (0, u, v))
        patch = spline(PA(pts), True, 4)
        cv.gouache(patch, (0.66, 0.36, 0.26), color2=(0.6, 0.3, 0.24), key=k + f"bp{c0}", tex=0.2, boil=False)
        lines = []
        for zz in np.arange(z0, z1, 16):
            if wall == "A":
                lines.append((PA([(c0 - 10, 0, zz), (c1 + 10, 0, zz)]), False, 0.9))
            else:
                lines.append((PA([(0, c0 - 10, zz), (0, c1 + 10, zz)]), False, 0.9))
            off = 0 if int(zz / 16) % 2 else 18
            for u in np.arange(c0 + off, c1, 36):
                pp = [(u, 0, zz), (u, 0, zz + 16)] if wall == "A" else [(0, u, zz), (0, u, zz + 16)]
                lines.append((PA(pp), False, 0.8))
        cv.ink(lines, key=k + f"bl{c0}", boil=False, alpha=0.6, sketch=False, jitter=0.5, clip=[patch])
        cv.ink([(patch, True, 1.2)], key=k + f"bpl{c0}", boil=False)
    # cracks
    for j in range(6):
        x, z = rng.uniform(60, L - 60), rng.uniform(200, HW - 60)
        pts = [(x, z)]
        for s in range(5):
            x += rng.uniform(-14, 14)
            z -= rng.uniform(8, 18)
            pts.append((x, z))
        pp = PA([(a, 0, b) for a, b in pts]) if j % 2 else PA([(0, a, b) for a, b in pts])
        cv.ink([(pp, False, 0.9)], key=k + f"cr{j}", boil=False, alpha=0.7)
    # wainscot panelling
    for wall in "AB":
        q = quadA(0, L, 0, 130) if wall == "A" else quadB(0, L, 0, 130)
        cv.gouache(q, (0.36, 0.22, 0.15) if wall == "A" else (0.30, 0.19, 0.13), key=k + "wn" + wall, tex=0.15,
                   boil=False, shade_dir=(0, 1), shade=0.2)
        cv.hatch(q, angle=90, spacing=5, alpha=0.3, key=k + "wnh" + wall, boil=False)
        strokes = []
        rail = PA([(0, 0, 130), (L, 0, 130)]) if wall == "A" else PA([(0, 0, 130), (0, L, 130)])
        rail2 = PA([(0, 0, 118), (L, 0, 118)]) if wall == "A" else PA([(0, 0, 118), (0, L, 118)])
        strokes += [(rail, False, 1.6), (rail2, False, 1.0)]
        for u in np.arange(20, L, 95):
            pr = [(u, 0, 18), (u + 75, 0, 18), (u + 75, 0, 100), (u, 0, 100)] if wall == "A" else \
                [(0, u, 18), (0, u + 75, 18), (0, u + 75, 100), (0, u, 100)]
            strokes.append((PA(pr), True, 1.0))
        cv.ink(strokes, key=k + "wnl" + wall, boil=False)
    cv.ink([(PA([(0, 0, 0), (0, 0, HW)]), False, 1.6)], key=k + "corner", boil=False)
    # corner shadow
    cv.shadow(PA([(0, 0, 0), (60, 0, 0), (60, 0, HW), (0, 0, HW)]), 0.35, 14)
    cv.shadow(PA([(0, 0, 0), (0, 60, 0), (0, 60, HW), (0, 0, HW)]), 0.35, 14)

    # ---- window on wall A
    wx0, wx1, wz0, wz1 = 300.0, 540.0, 250.0, 470.0
    rad = (wx1 - wx0) / 2
    arch3 = [(wx0, 0, wz0), (wx1, 0, wz0), (wx1, 0, wz1)]
    for t in np.linspace(0, math.pi, 18):
        arch3.append(((wx0 + wx1) / 2 + rad * math.cos(t), 0, wz1 + rad * math.sin(t)))
    arch3.append((wx0, 0, wz1))
    opening = PA(arch3)
    # outside: night sky + city
    cv.gouache(opening, (0.13, 0.17, 0.36), color2=(0.22, 0.18, 0.42), key=k + "sky", shade_dir=(0, 1), shade=-0.6,
               light=False, boil=False, jit=0)
    cv.wash(opening, (0.85, 0.5, 0.55), dens=0.35, soft=25, key=k + "dusk", hard=1.0, clip=[opening], boil=False,
            shift=(0, 60))
    mx, my = P(345, 0, 560)
    moon = ellipse(mx, my, 16, 16)
    cv.paint(moon, (1.0, 0.95, 0.8))
    cv.light((mx, my), 30, (0.8, 0.8, 1.0), 0.35)
    for j in range(14):
        a, b = P(rng.uniform(wx0 + 10, wx1 - 10), 0, rng.uniform(wz0 + 120, wz1 + rad - 20))
        cv.paint(ellipse(a, b, 1.5, 1.5, n=6), (1, 0.97, 0.85), 0.8)
    bl = P(wx0, 0, wz0)
    br = P(wx1, 0, wz0)
    city = []
    xs = np.linspace(bl[0], br[0], 9)
    for i2 in range(8):
        hgt = rng.uniform(40, 120)
        ya = bl[1] + (xs[i2] - bl[0]) * (br[1] - bl[1]) / (br[0] - bl[0])
        yb = bl[1] + (xs[i2 + 1] - bl[0]) * (br[1] - bl[1]) / (br[0] - bl[0])
        city += [(xs[i2], ya - hgt), (xs[i2 + 1], yb - hgt)]
    city = np.array([(bl[0], bl[1])] + city + [(br[0], br[1])], float)
    cv.gouache(city, (0.09, 0.09, 0.18), key=k + "city", light=False, boil=False, clip=[opening])
    for j in range(40):
        u = rng.uniform(bl[0] + 4, br[0] - 4)
        yb = bl[1] + (u - bl[0]) * (br[1] - bl[1]) / (br[0] - bl[0])
        v = yb - rng.uniform(6, 100)
        win = np.array([(u, v), (u + 4, v + 2.3), (u + 4, v + 7.3), (u, v + 5)], float)
        cv.paint(win, (1.0, 0.82, 0.45), rng.uniform(0.5, 1.0))
    # frame + jamb + sill
    jamb = PA([(wx0, 0, wz0), (wx0, -WALLT, wz0), (wx0, -WALLT, wz1), (wx0, 0, wz1)])
    cv.gouache(jamb, (0.70, 0.52, 0.40), key=k + "jamb", boil=False)
    sill = PA([(wx0 - 14, 14, wz0), (wx1 + 14, 14, wz0), (wx1 + 14, -WALLT, wz0), (wx0 - 14, -WALLT, wz0)])
    cv.gouache(sill, (0.88, 0.82, 0.70), key=k + "sill", boil=False)
    frame = []
    for t in np.linspace(0, math.pi, 18):
        frame.append(((wx0 + wx1) / 2 + rad * math.cos(t), 0, wz1 + rad * math.sin(t)))
    fr = PA([(wx1, 0, wz0), (wx1, 0, wz1)] + frame + [(wx0, 0, wz1), (wx0, 0, wz0)])
    mull = [PA([((wx0 + wx1) / 2, 0, wz0), ((wx0 + wx1) / 2, 0, wz1 + rad)]), PA([(wx0, 0, 380), (wx1, 0, 380)])]
    cv.ink([(fr, False, 6.0)], color=(0.32, 0.36, 0.30), key=k + "frm", boil=False, sketch=False, alpha=1)
    cv.ink([(m, False, 4.0) for m in mull], color=(0.32, 0.36, 0.30), key=k + "mul", boil=False, sketch=False, alpha=1)
    cv.ink([(fr, False, 1.4), (sill, True, 1.2)] + [(m, False, 1.0) for m in mull], key=k + "frl", boil=False)
    # shutters
    for side, xa, xb in (("l", wx0 - 70, wx0 - 8), ("r", wx1 + 8, wx1 + 70)):
        sh = quadA(xa, xb, wz0, wz1 + 40)
        cv.gouache(sh, (0.30, 0.45, 0.36), color2=(0.26, 0.40, 0.38), key=k + "sh" + side, boil=False)
        sl = [(PA([(xa + 4, 0, zz), (xb - 4, 0, zz)]), False, 0.9) for zz in np.arange(wz0 + 12, wz1 + 36, 13)]
        cv.ink([(sh, True, 1.3)] + sl, key=k + "shl" + side, boil=False)
    # flower box
    box(cv, wx0 - 10, wx1 + 10, 0, 24, wz0 - 36, wz0 - 6, (0.55, 0.30, 0.20), k + "fbox")
    for j in range(14):
        a, b = P(rng.uniform(wx0, wx1), 12, wz0 - 4)
        c = (0.85, 0.25, 0.3) if j % 3 else (0.95, 0.75, 0.3)
        leaf = ellipse(a + rng.uniform(-6, 6), b - rng.uniform(4, 16), 9, 6, rot=rng.uniform(0, 3))
        cv.gouache(leaf, (0.28, 0.48, 0.25), key=k + f"fl{j}", boil=False)
        cv.paint(ellipse(a, b - rng.uniform(10, 22), 4, 4, n=8), c, light=True)

    # ---- wall B: shelves with bottles + cabinet + painting + sconce
    box(cv, 0, 70, 120, 420, 0, 150, (0.42, 0.25, 0.16), k + "cab")
    for u in (195, 345):
        door = PA([(70, u - 60, 20), (70, u + 60, 20), (70, u + 60, 130), (70, u - 60, 130)])
        cv.ink([(door, True, 1.0)], key=k + f"cd{u}", boil=False)
    for zs in (300, 400):
        box(cv, 0, 36, 130, 410, zs - 8, zs, (0.48, 0.30, 0.18), k + f"shelf{zs}", hatch_sides=False)
        cv.shadow(PA([(0, 130, zs - 8), (0, 410, zs - 8), (0, 410, zs - 40), (0, 130, zs - 40)]), 0.3, 6)
        for j, yy in enumerate(np.arange(150, 400, 30)):
            col = [(0.16, 0.30, 0.18), (0.45, 0.22, 0.10), (0.20, 0.26, 0.16), (0.55, 0.16, 0.18)][(j + zs) % 4]
            bottle(cv, 18, yy, zs, rng.uniform(55, 80), 8, col, k + f"bt{zs}{j}")
    for zs, items in ((150, 4),):
        for j in range(items):
            bottle(cv, 30, 160 + j * 60, 150, 70, 9, (0.2, 0.3, 0.2), k + f"ct{j}")
    pic = quadB(470, 640, 300, 450)
    cv.gouache(pic, (0.40, 0.26, 0.14), key=k + "pic", boil=False)
    inner = quadB(484, 626, 314, 436)
    cv.gouache(inner, (0.70, 0.75, 0.66), color2=(0.85, 0.7, 0.5), key=k + "pin", boil=False)
    hill = PA([(0, 484, 314), (0, 530, 380), (0, 580, 350), (0, 626, 400), (0, 626, 314)])
    cv.gouache(hill, (0.42, 0.55, 0.36), key=k + "phl", boil=False)
    cv.ink([(pic, True, 1.4), (inner, True, 1.0)], key=k + "pic", boil=False)
    # sconce
    sx_, sy_ = P(0, 600, 430)
    sc = spline([(sx_ - 16, sy_ - 10), (sx_ + 16, sy_ - 1), (sx_ + 12, sy_ + 22), (sx_ - 12, sy_ + 14)], True)
    cv.paint(sc, (1.0, 0.85, 0.55))
    cv.ink([(sc, True, 1.3)], key=k + "sc", boil=False)

    # ---- clock + plant on wall A
    cx_, cy_ = P(640, 0, 520)
    clock = ellipse(cx_, cy_, 34, 40, rot=math.radians(30), n=30)
    cv.gouache(clock, (0.92, 0.88, 0.76), key=k + "clk", boil=False)
    cv.ink([(clock, True, 2.2), ([(cx_, cy_), (cx_ + 4, cy_ - 22)], False, 1.6),
            ([(cx_, cy_), (cx_ + 16, cy_ + 12)], False, 1.6)], key=k + "clk", boil=False)
    # big potted plant in right back
    box(cv, 660, 730, 30, 100, 0, 90, (0.62, 0.34, 0.24), k + "pot")
    px_, py_ = P(695, 65, 90)
    for j in range(16):
        ang = rng.uniform(-2.6, -0.5)
        ln = rng.uniform(60, 150)
        tip = (px_ + math.cos(ang) * ln, py_ + math.sin(ang) * ln)
        leaf = spline([(px_, py_), ((px_ + tip[0]) / 2 + 14 * math.sin(ang), (py_ + tip[1]) / 2 - 14 * math.cos(ang)),
                       tip, ((px_ + tip[0]) / 2 - 14 * math.sin(ang), (py_ + tip[1]) / 2 + 14 * math.cos(ang))], True, 6)
        cv.gouache(leaf, (0.26, 0.46, 0.28), color2=(0.2, 0.38, 0.32), key=k + f"pl{j}", boil=False, shade=0.3)
        cv.ink([(leaf, True, 1.1), ([(px_, py_), tip], False, 0.8)], key=k + f"pl{j}", boil=False)

    # ---- wall tops (cut-away thickness) + end faces
    topA = PA([(-WALLT, -WALLT, HW), (L, -WALLT, HW), (L, 0, HW), (0, 0, HW), (0, L, HW), (-WALLT, L, HW)])
    cv.gouache(topA, (0.90, 0.82, 0.70), key=k + "top", boil=False, light=False)
    endA = PA([(L, 0, -SLAB), (L, -WALLT, -SLAB), (L, -WALLT, HW), (L, 0, HW)])
    endB = PA([(0, L, -SLAB), (-WALLT, L, -SLAB), (-WALLT, L, HW), (0, L, HW)])
    cv.gouache(endA, (0.62, 0.50, 0.42), key=k + "endA", boil=False, light=False)
    cv.gouache(endB, (0.70, 0.58, 0.48), key=k + "endB", boil=False, light=False)
    cv.hatch(endA, angle=60, spacing=4, alpha=0.5, key=k + "hea", boil=False)
    cv.hatch(endB, angle=120, spacing=5, alpha=0.4, key=k + "heb", boil=False)
    cv.ink([(topA, True, 1.6), (endA, True, 1.6), (endB, True, 1.6), (wa, True, 1.6), (wb, True, 1.6)],
           key=k + "walls", boil=False)

    # ---- floor
    fl = PA([(0, 0, 0), (L, 0, 0), (L, L, 0), (0, L, 0)])
    cv.gouache(fl, (0.56, 0.37, 0.23), color2=(0.48, 0.30, 0.20), key=k + "floor", shade=0.1, tex=0.15, boil=False)
    planks = []
    for yy in np.arange(38, L, 38):
        planks.append((PA([(0, yy, 0), (L, yy, 0)]), False, 0.9))
        for xx in np.arange(rng.uniform(0, 160), L, rng.uniform(160, 260)):
            planks.append((PA([(xx, yy - 38, 0), (xx, yy, 0)]), False, 0.8))
    cv.ink(planks, key=k + "pl", boil=False, alpha=0.6)
    cv.hatch(fl, angle=ANG_X, spacing=6, alpha=0.18, key=k + "flh", boil=False)
    cv.hatch(fl, angle=ANG_Y, spacing=6, alpha=0.25, key=k + "flh2", boil=False, fade=((0, 1), 0.55, 1.0))
    # wall/floor contact shadows
    cv.shadow(PA([(0, 0, 0), (L, 0, 0), (L, 50, 0), (0, 50, 0)]), 0.45, 10)
    cv.shadow(PA([(0, 0, 0), (0, L, 0), (50, L, 0), (50, 0, 0)]), 0.45, 10)
    # rug
    rug = circ3(390, 390, 280, 0.5, 60)
    cv.gouache(rug, (0.46, 0.18, 0.18), color2=(0.40, 0.16, 0.22), key=k + "rug", tex=0.14, boil=False)
    border = circ3(390, 390, 252, 0.5, 60)
    cv.ink([(rug, True, 1.4), (border, True, 1.0), (circ3(390, 390, 240, 0.5, 60), True, 0.8)],
           key=k + "rug", boil=False)
    for j in range(24):
        a = j / 24 * 2 * math.pi
        p0 = P(390 + 246 * math.cos(a), 390 + 246 * math.sin(a), 0.5)
        cv.paint(ellipse(p0[0], p0[1], 3.2, 1.8, n=8), (0.85, 0.65, 0.3), 0.9, light=True)

    # ---- empty table for two in the back right

    # ---- pendant lamp + string lights
    SCALE[0] = 1.0
    lx, ly = P(390, 390, LAMP_Z)
    SCALE[0] = RS
    cv.ink([([(lx, -50), (lx, ly - 48)], False, 1.4)], key=k + "cord", boil=False, sketch=False)
    shade_p = spline([(lx - 62, ly), (lx - 50, ly - 26), (lx - 18, ly - 46), (lx, ly - 48), (lx + 18, ly - 46),
                      (lx + 50, ly - 26), (lx + 62, ly)], n=6)
    shade_p = np.vstack([shade_p, ellipse(lx, ly, 62, 12, n=18, a0=0, a1=math.pi)])
    cv.gouache(shade_p, (0.28, 0.34, 0.30), color2=(0.32, 0.30, 0.26), key=k + "shade", boil=False,
               shade_dir=(1, 0), shade=0.4, light=False)
    cv.paint(ellipse(lx, ly, 58, 10), (1.0, 0.93, 0.68))
    cv.ink([(shade_p, True, 1.6), (ellipse(lx, ly, 62, 12), True, 1.2)], key=k + "shade", boil=False)
    for wall in "AB":
        pts = []
        for t in np.linspace(0, 1, 60):
            u = t * (L - 20) + 10
            sag = 26 * abs(math.sin(t * math.pi * 5))
            pts.append((u, 6, HW - 24 - sag) if wall == "A" else (6, u, HW - 24 - sag))
        wire = PA(pts)
        cv.ink([(wire, False, 0.9)], key=k + "wire" + wall, boil=False, sketch=False)
        for t in np.linspace(0.05, 0.95, 10):
            q = wire[int(t * 59)]
            cv.paint(ellipse(q[0], q[1] + 7, 4.5, 6, n=10), (1.0, 0.88, 0.55))
            cv.light((q[0], q[1] + 7), 22, (1.0, 0.75, 0.4), 0.5)
    # baked glows
    cv.light((lx, ly + 4), 95, (1.0, 0.78, 0.45), 0.5)
    cv.light(P(0, 600, 430), 60, (1.0, 0.75, 0.4), 0.55)


def side_table(cv, x, y, k):
    top = circ3(x, y, 62, 75, 40)
    cv.shadow(circ3(x + 10, y + 10, 75, 0, 30), 0.4, 8)
    leg = PA([(x, y, 0), (x, y, 75)])
    cv.ink([(leg, False, 5.0)], color=(0.25, 0.16, 0.1), key=k + "leg", boil=False, sketch=False, alpha=1)
    cv.gouache(top, (0.88, 0.84, 0.76), key=k + "top", boil=False)
    cv.ink([(top, True, 1.4)], key=k + "top", boil=False)
    cx, cy = P(x, y, 75)
    cv.paint(rrect(cx - 4, cy - 26, cx + 4, cy, 2), (0.95, 0.9, 0.8), light=True)
    cv.paint(ellipse(cx, cy - 31, 3, 6), (1.0, 0.85, 0.5))
    cv.light((cx, cy - 31), 30, (1.0, 0.7, 0.35), 0.5)
    for dx, dy in ((-80, 0), (80, 0)) if x > y else ((0, -80), (0, 80)):
        chair_iso(cv, x + dx, y + dy, k + f"c{dx}{dy}", facing=(-np.sign(dx), -np.sign(dy)))


def chair_iso(cv, x, y, k, facing=(1, 0), col=(0.40, 0.24, 0.15)):
    """simple bistro chair; facing = unit vector toward table in iso xy"""
    fx, fy = facing
    s = 22
    seat = PA([(x - s, y - s, 45), (x + s, y - s, 45), (x + s, y + s, 45), (x - s, y + s, 45)])
    legs = []
    for dx, dy in ((-s, -s), (s, -s), (s, s), (-s, s)):
        legs.append((PA([(x + dx, y + dy, 0), (x + dx, y + dy, 45)]), False, 2.2))
    cv.ink(legs, color=(0.22, 0.13, 0.09), key=k + "lg", boil=False, sketch=False, alpha=1)
    cv.gouache(seat, col, key=k + "seat", boil=False)
    bx, by = x - fx * s, y - fy * s
    px, py = -fy, fx
    back = PA([(bx - px * s, by - py * s, 45), (bx + px * s, by + py * s, 45), (bx + px * s, by + py * s, 110),
               (bx - px * s, by - py * s, 110)])
    cv.gouache(back, np.asarray(col) * 0.85, key=k + "back", boil=False, alpha=0.95)
    cv.ink([(seat, True, 1.2), (back, True, 1.2)], key=k + "ch", boil=False)
