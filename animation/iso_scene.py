"""Date night - characters, props, sets and the 15 s timeline."""
import math
from types import SimpleNamespace as NS

import numpy as np

from wc import (Canvas, ellipse, rrect, spline, xf, clip_halfplane, INK)
import iso_bg as iso

D2R = math.pi / 180
FPS_DRAW = 12            # drawings per second ("on twos" at 24 fps)
N_DRAWINGS = 180         # 15 s

# shot list: (first drawing, kind)
SHOTS = [(0, "wide"), (51, "tight"), (69, "wide"), (86, "phone"), (128, "tight"), (144, "wide")]


def cam_for(i):
    """world camera (cx, cy, zoom): the whole isometric diorama stays in frame; only gentle push-ins."""
    t = i / FPS_DRAW
    if shot_for(i) == "phone":
        return (540.0, 960.0, 1.0)
    z = key(t, [(0, 1.0), (3.3, 1.04), (4.25, 1.08), (5.75, 1.08), (7.17, 1.06), (10.67, 1.08), (12.0, 1.08),
                (13.4, 1.06), (15.0, 1.0)])
    return (540.0, 985.0, z)


def shot_for(i):
    k = SHOTS[0][1]
    for d, kind in SHOTS:
        if i >= d:
            k = kind
    return k


# ---------------------------------------------------------------- palette
SKIN_W, SKIN_W2 = (0.98, 0.80, 0.68), (0.96, 0.72, 0.62)
SKIN_M, SKIN_M2 = (0.90, 0.67, 0.53), (0.86, 0.60, 0.48)
HAIR_W, HAIR_W2 = (0.56, 0.22, 0.12), (0.42, 0.16, 0.10)
HAIR_M, HAIR_M2 = (0.27, 0.17, 0.12), (0.22, 0.14, 0.13)
DRESS, DRESS2 = (0.16, 0.50, 0.44), (0.12, 0.38, 0.47)
NAVY, NAVY2 = (0.20, 0.26, 0.45), (0.25, 0.28, 0.52)
SHIRT = (0.90, 0.92, 0.96)
WINE, WINE2 = (0.48, 0.05, 0.14), (0.62, 0.10, 0.20)
GOLD = (0.88, 0.68, 0.30)
BLUSH = (0.95, 0.48, 0.48)
WARM = (1.0, 0.78, 0.45)


# ---------------------------------------------------------------- keyframes
def ease(u):
    return u * u * (3 - 2 * u)


def key(t, kf):
    if t <= kf[0][0]:
        return np.asarray(kf[0][1], float) if isinstance(kf[0][1], tuple) else kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = ease((t - t0) / max(t1 - t0, 1e-6))
            if isinstance(v0, tuple):
                v0, v1 = np.asarray(v0, float), np.asarray(v1, float)
            return v0 + (v1 - v0) * u
    v = kf[-1][1]
    return np.asarray(v, float) if isinstance(v, tuple) else v


def in_any(t, spans):
    return any(a <= t < b for a, b in spans)


BUZZ = [(3.30, 3.92), (4.30, 4.92), (5.25, 5.75)]


# ---------------------------------------------------------------- poses
def pose_w(t):
    osc = abs(math.sin(2 * math.pi * 2.4 * t))
    laugh = key(t, [(0, 1), (1.35, 1), (1.55, 0), (2.75, 0), (2.9, 1), (3.3, 1), (3.4, 0), (13.0, 0), (13.25, 1), (15, 1)])
    p = NS()
    p.laugh, p.osc = laugh, osc
    p.lean = key(t, [(0, -2), (1.4, -2), (1.7, 1), (3.3, 1), (3.5, 5), (4.25, 4), (4.4, 2), (5.75, 2), (6.2, 5),
                     (7.17, 6), (10.67, 2), (11.3, -1), (12.0, 0), (12.2, -2), (12.5, 6), (12.75, 5), (13.2, 0), (15, -1)])
    p.bob = laugh * 7 * osc
    p.tilt = key(t, [(0, 9), (1.3, 11), (1.6, 0), (2.75, 0), (2.95, 9), (3.3, 9), (3.45, -8), (4.25, -8), (4.3, 0),
                     (5.2, 0), (5.35, -12), (5.55, -2), (5.75, -7), (7.17, -7), (10.67, 0), (11.2, 5), (12.0, 3),
                     (12.3, 0), (12.6, -2), (13.0, 8), (15, 8)]) + laugh * 4 * osc
    p.happy = key(t, [(0, 1), (1.4, 1), (1.5, 0), (2.8, 0), (2.9, 1), (3.35, 1), (3.42, 0), (11.4, 0), (11.55, 1),
                      (12.2, 1), (12.3, 0), (13.05, 0), (13.15, 1), (15, 1)])
    p.open = key(t, [(0, 1), (3.38, 1), (3.5, 1.28), (4.0, 1.12), (10.67, 1.08), (11.0, 1.0), (15, 1.0)])
    for bt in (2.1, 4.95, 6.95, 11.05):
        if bt <= t < bt + 0.09:
            p.open = 0.05
    p.look = key(t, [(0, (1, 0)), (3.35, (1, 0)), (3.45, (0.8, 1)), (4.25, (0.8, 1)), (4.3, (1, 0)), (5.75, (1, 0)),
                     (5.8, (1, 0.7)), (7.17, (1, 0.7)), (10.67, (1, 0.1)), (15, (1, 0))])
    p.raise_ = key(t, [(0, 0.3), (3.38, 0.3), (3.5, 1), (4.25, 0.8), (4.5, 0.4), (10.67, 0.4), (11.0, 0.3), (15, 0.3)])
    p.worry = key(t, [(0, 0), (3.4, 0), (3.7, 0.5), (4.25, 0.6), (4.5, 1), (7.17, 1), (10.67, 1), (11.1, 0.1), (11.3, 0), (15, 0)])
    p.smile = key(t, [(0, 1), (3.35, 1), (3.45, 0), (4.25, -0.2), (4.5, -0.6), (7.17, -0.6), (10.67, -0.5), (11.0, 0.5),
                      (11.3, 1), (15, 1)])
    base = key(t, [(0, 0.1), (1.4, 0.1), (1.6, 0.05), (3.4, 0.05), (3.45, 0.35), (4.1, 0.3), (4.25, 0), (10.67, 0),
                   (11.3, 0.25), (12.0, 0.2), (12.2, 0.1), (12.5, 0.45), (12.8, 0.4), (13.0, 0.2), (15, 0.2)])
    p.mopen = base + laugh * (0.32 + 0.3 * osc)
    p.mw = key(t, [(0, 46), (3.4, 46), (3.45, 26), (4.25, 26), (4.3, 34), (10.67, 34), (11.2, 46), (15, 46)])
    p.mwob = key(t, [(0, 0), (4.25, 0), (4.35, 1), (10.67, 1), (10.9, 0)])
    p.blush = key(t, [(0, 0.55), (3.4, 0.55), (3.6, 0.2), (10.67, 0.2), (11.4, 0.8), (15, 0.8)])
    p.handA = key(t, [(0, (410, 1185)), (0.7, (412, 1172)), (1.4, (415, 1185)), (2.0, (420, 1200)), (3.3, (418, 1195)),
                      (3.45, (420, 1215)), (4.25, (425, 1225)), (5.75, (428, 1240)), (6.2, (440, 1352)),
                      (12.0, (440, 1352)), (12.15, (430, 1362)), (12.48, (498, 1000)), (12.55, (498, 1000)),
                      (12.7, (484, 1010)), (13.3, (430, 1170)), (15, (425, 1180))]) + (0, laugh * 5 * osc)
    p.gtilt = key(t, [(0, -4), (3.3, -4), (5.75, 0), (12.3, 0), (12.48, 8), (12.55, 6), (12.75, 0), (13.3, -3), (15, -3)])
    p.handB = key(t, [(0, (262, 1392)), (4.5, (262, 1392)), (4.9, (318, 1125)), (10.67, (318, 1125)), (11.2, (312, 1110)),
                      (11.9, (318, 1125)), (12.1, (262, 1392)), (15, (262, 1392))])
    p.modeB = "chest" if p.handB[1] < 1300 else "flat"
    p.sweat = None
    p.phone = False
    p.fx = 34
    return p


def pose_m(t):
    osc = abs(math.sin(2 * math.pi * 2.2 * t + 1.0))
    laugh = key(t, [(0, 1), (1.35, 1), (1.5, 0), (2.75, 0), (2.9, 1), (3.3, 1), (3.4, 0), (13.0, 0), (13.2, 1), (15, 1)])
    talk = key(t, [(0, 0), (1.45, 0), (1.55, 1), (2.65, 1), (2.8, 0)])
    p = NS()
    p.laugh, p.osc = laugh, osc
    p.lean = key(t, [(0, -1), (1.5, 2), (2.7, 3), (3.3, 1), (3.5, 5), (4.25, 4), (4.4, 2), (5.75, 2), (6.0, 7), (6.3, 7),
                     (6.9, 3), (7.17, 3), (10.67, 3), (11.0, 0), (11.6, 2), (12.2, -2), (12.5, 6), (12.75, 5),
                     (13.2, 0), (15, 1)])
    p.bob = laugh * 7 * osc
    p.tilt = key(t, [(0, 10), (1.4, 10), (1.6, 0), (2.75, 0), (2.95, 8), (3.3, 8), (3.45, -10), (4.25, -10), (4.3, 0),
                     (5.75, 0), (5.9, -12), (7.17, -12), (10.67, -6), (10.9, 6), (11.2, 4), (12.0, 2), (12.6, -2),
                     (13.0, 9), (15, 9)]) + laugh * 4 * osc + talk * 2 * math.sin(2 * math.pi * 1.6 * t)
    p.happy = key(t, [(0, 1), (1.45, 1), (1.55, 0), (2.8, 0), (2.9, 1), (3.35, 1), (3.42, 0), (11.25, 0), (11.35, 1),
                      (12.2, 1), (12.3, 0), (13.05, 0), (13.15, 1), (15, 1)])
    p.open = key(t, [(0, 1), (3.38, 1), (3.5, 1.3), (4.0, 1.12), (10.67, 1.05), (10.75, 0.05), (11.15, 0.05),
                     (11.25, 1), (15, 1)])
    for bt in (1.95, 5.05, 14.2):
        if bt <= t < bt + 0.09:
            p.open = 0.05
    p.look = key(t, [(0, (1, 0)), (3.35, (1, 0)), (3.45, (0.5, 1)), (4.25, (0.5, 1)), (4.3, (1, 0)), (5.75, (1, 0)),
                     (5.85, (0.6, 1)), (6.3, (0.6, 1)), (6.6, (0.3, 1)), (7.17, (0.3, 1)), (10.67, (0.2, 1)),
                     (10.9, (1, 0)), (15, (1, 0))])
    p.raise_ = key(t, [(0, 0.3), (3.38, 0.3), (3.5, 1), (4.25, 0.8), (4.5, 0.4), (10.67, 0.4), (11.0, 0.3), (15, 0.3)])
    p.worry = key(t, [(0, 0), (3.4, 0), (3.7, 0.5), (4.25, 0.6), (4.5, 1), (7.17, 1), (10.67, 0.8), (10.8, 0), (15, 0)])
    p.smile = key(t, [(0, 1), (3.35, 1), (3.45, 0), (4.25, -0.3), (4.5, -0.7), (7.17, -0.6), (10.67, -0.3), (10.8, 0.2),
                      (11.2, 1), (15, 1)])
    base = key(t, [(0, 0.1), (3.4, 0.05), (3.45, 0.3), (4.1, 0.3), (4.25, 0), (10.67, 0), (10.75, 0.15), (11.1, 0.1),
                   (11.3, 0.35), (12.0, 0.3), (12.2, 0.1), (12.5, 0.5), (12.8, 0.45), (13.0, 0.2), (15, 0.2)])
    p.mopen = base + laugh * (0.32 + 0.3 * osc) + talk * 0.34 * abs(math.sin(2 * math.pi * 3.2 * t))
    p.mw = key(t, [(0, 48), (3.4, 48), (3.45, 28), (4.25, 28), (4.3, 40), (10.67, 40), (10.75, 24), (11.1, 24),
                   (11.25, 50), (15, 50)])
    p.mwob = key(t, [(0, 0), (4.25, 0), (4.35, 1), (10.67, 1), (10.75, 0)])
    p.blush = key(t, [(0, 0.35), (3.4, 0.35), (3.6, 0.1), (10.67, 0.1), (11.4, 0.5), (15, 0.5)])
    p.handA = key(t, [(0, (662, 1188)), (1.45, (660, 1185)), (1.7, (632, 1110)), (2.0, (655, 1150)), (2.3, (630, 1105)),
                      (2.6, (650, 1170)), (2.85, (662, 1188)), (3.3, (662, 1190)), (3.45, (662, 1215)),
                      (4.25, (664, 1230)), (5.75, (664, 1240)), (5.95, (640, 1352)), (12.0, (640, 1352)),
                      (12.15, (650, 1362)), (12.48, (582, 1000)), (12.55, (582, 1000)), (12.7, (598, 1010)),
                      (13.3, (655, 1170)), (15, (660, 1180))]) + (0, laugh * 5 * osc)
    p.gtilt = key(t, [(0, -3), (1.45, -3), (1.7, -10), (2.0, -4), (2.3, -10), (2.6, -3), (5.75, 0), (12.3, 0),
                      (12.48, 8), (12.55, 6), (12.75, 0), (13.3, -3), (15, -3)])
    p.handB = key(t, [(0, (820, 1392)), (5.8, (820, 1392)), (6.15, (742, 1446)), (6.3, (742, 1446)), (6.85, (700, 1140)),
                      (7.17, (698, 1135)), (10.67, (698, 1135)), (10.95, (705, 1250)), (11.2, (742, 1446)),
                      (11.35, (742, 1446)), (11.7, (820, 1392)), (15, (820, 1392))])
    p.phone = 6.3 <= t < 11.25
    p.modeB = "phone" if p.phone else "flat"
    p.sweat = (t - 4.45) / 1.3 if 4.45 <= t < 7.17 else None
    p.fx = 34
    return p


# ---------------------------------------------------------------- characters
class Char:
    def __init__(self, name, d, neck, skin, skin2, hair, hair2, female):
        self.name, self.dir, self.neck0 = name, d, np.array(neck, float)
        self.skin, self.skin2, self.hair, self.hair2, self.female = skin, skin2, hair, hair2, female

    def frame(self, p):
        a = self.dir * p.lean * D2R
        hip = self.neck0 + (0, 380)
        c, s = math.cos(a), math.sin(a)
        neck = hip + np.array([-s * -380, c * -380]) + (0, p.bob)
        # head centre: above neck, nudged toward facing side
        off = np.array([self.dir * 12, -118])
        hc = neck + np.array([c * off[0] - s * off[1], s * off[0] + c * off[1]])
        hc[1] += p.bob * 0.6
        hr = a - self.dir * p.tilt * D2R
        shA = xf([(118, 44)], neck, a, 1, self.dir)[0]
        shB = xf([(-118, 44)], neck, a, 1, self.dir)[0]
        return NS(a=a, neck=neck, hc=hc, hr=hr, shA=shA, shB=shB)


WOMAN = Char("w", 1, (275, 975), SKIN_W, SKIN_W2, HAIR_W, HAIR_W2, True)
MAN = Char("m", -1, (805, 968), SKIN_M, SKIN_M2, HAIR_M, HAIR_M2, False)

HEAD = [(0, -125), (60, -113), (98, -62), (106, 0), (97, 56), (66, 101), (24, 124), (-20, 121), (-68, 99), (-98, 50),
        (-104, -12), (-91, -76), (-54, -114)]
EAR = [(-92, -18), (-118, -24), (-127, 6), (-116, 36), (-94, 34)]
W_BACKHAIR = [(-10, -146), (70, -132), (118, -72), (128, 10), (116, 96), (124, 180), (96, 236), (52, 214), (10, 250),
              (-60, 268), (-132, 286), (-172, 214), (-160, 108), (-150, -10), (-128, -96), (-76, -138)]
W_FRONTHAIR = [(-108, 22), (-118, -52), (-90, -116), (-20, -146), (54, -136), (104, -92), (118, -30), (112, 18),
               (98, -26), (76, -60), (40, -66), (8, -82), (-26, -58), (-58, -42), (-86, -6)]
M_HAIR = [(-108, 6), (-114, -58), (-86, -114), (-30, -146), (36, -154), (92, -128), (112, -80), (104, -46),
          (74, -70), (36, -80), (-6, -74), (-46, -60), (-72, -34), (-82, 4), (-88, 34), (-100, 30)]
M_BEARD = [(-98, 24), (-92, 70), (-62, 108), (-14, 132), (30, 130), (72, 106), (100, 58), (106, 18), (92, 40),
           (66, 70), (46, 98), (26, 106), (6, 104), (-18, 94), (-44, 64), (-74, 40)]


def draw_back_hair(cv, ch, p, F, k):
    if not ch.female:
        return
    sway = math.sin(F.hr * 2) * 10
    pts = np.array(W_BACKHAIR, float)
    pts[pts[:, 1] > 120, 0] += sway
    poly = xf(spline(pts, True), F.hc, F.hr, 1, ch.dir)
    cv.fill(poly, ch.hair, dens=0.85, color2=ch.hair2, key=k + "bh", anchor=F.hc)
    cv.ink([(poly, True)], 3.6, key=k + "bh")
    cv.ink([(xf(spline([(-120, 40), (-138, 140), (-120, 230)]), F.hc, F.hr, 1, ch.dir), False, 2.2),
            (xf(spline([(108, 110), (112, 190), (96, 226)]), F.hc, F.hr, 1, ch.dir), False, 2.2)],
           key=k + "bhs", alpha=0.6)


def draw_torso(cv, ch, p, F, k):
    T = lambda pts: xf(pts, F.neck, F.a, 1, ch.dir)
    if ch.female:
        skin = T(spline([(-34, -80), (-36, -6), (-78, 8), (-126, 26), (-152, 62), (-156, 140), (-128, 300), (-138, 440), (-120, 560), (150, 560), (150, 440), (132, 300),
                         (156, 140), (152, 62), (126, 26), (78, 8), (36, -6), (34, -80)], True))
        cv.fill(skin, ch.skin, dens=0.55, color2=ch.skin2, key=k + "sk", anchor=F.neck)
        cv.wash(T(ellipse(4, -6, 40, 26)), ch.skin2, dens=0.45, knock=False, key=k + "nsh", anchor=F.neck, soft=5)
        cv.ink([(skin, True)], 3.4, key=k + "sk")
        dress = T(spline([(-156, 116), (-130, 82), (-84, 94), (-42, 126), (-10, 140), (0, 132), (10, 140), (42, 126),
                          (84, 94), (130, 82), (156, 116), (134, 300), (152, 440), (150, 568), (-122, 568), (-140, 440), (-130, 300)], True))
        cv.fill(dress, DRESS, dens=0.82, color2=DRESS2, key=k + "dr", anchor=F.neck)
        cv.wash(T(spline([(60, 140), (120, 160), (140, 300), (130, 430), (70, 430), (90, 300)], True)), DRESS2,
                dens=0.35, knock=False, key=k + "drs", anchor=F.neck, soft=8)
        cv.hatch(dress, angle=60, spacing=4.5, alpha=0.45, key=k + "drh", fade=((-ch.dir, 0.4), 0.45, 1.0))
        cv.hatch(skin, angle=60, spacing=5, alpha=0.25, key=k + "skh", fade=((-ch.dir, 0.2), 0.75, 1.0))
        cv.ink([(dress, True)], 3.4, key=k + "dr")
        straps = [T(spline([(-96, 22), (-98, 60), (-104, 96)])), T(spline([(96, 22), (98, 60), (104, 96)]))]
        cv.ink([(s, False, 9) for s in straps], color=(0.12, 0.38, 0.36), alpha=0.95, key=k + "st")
        cv.ink([(T(spline([(-30, 8), (-14, 40), (0, 50), (14, 40), (30, 8)])), False, 1.6)], color=(0.6, 0.45, 0.2),
               key=k + "nl")
        pend = T(ellipse(0, 56, 6, 7))
        cv.fill(pend, GOLD, dens=0.9, key=k + "pd", soft=1.5, anchor=F.neck)
        cv.ink([(pend, True, 1.6)], key=k + "pd")
        cv.ink([(T(spline([(-62, 22), (-40, 30), (-22, 26)])), False, 1.8),
                (T(spline([(62, 22), (40, 30), (22, 26)])), False, 1.8)], alpha=0.5, key=k + "cb")
    else:
        shirt = T(spline([(-66, 8), (-40, -6), (0, 70), (40, -6), (66, 8), (44, 230), (-44, 230)], True))
        cv.fill(shirt, SHIRT, dens=0.5, key=k + "sh", anchor=F.neck)
        neckv = T(spline([(-32, -80), (-34, -2), (-12, 40), (0, 62), (12, 40), (34, -2), (32, -80)], True))
        cv.fill(neckv, ch.skin, dens=0.6, color2=ch.skin2, key=k + "nk", anchor=F.neck)
        cv.wash(T(ellipse(4, -8, 40, 26)), ch.skin2, dens=0.5, knock=False, key=k + "nsh", anchor=F.neck, soft=5)
        cv.ink([(neckv, False, 3.0)], key=k + "nk")
        collar = [T([(-40, -6), (-58, 34), (-20, 46), (0, 66)]), T([(40, -6), (58, 34), (20, 46), (0, 66)])]
        for i, c in enumerate(collar):
            cv.fill(c, SHIRT, dens=0.35, key=k + f"col{i}", anchor=F.neck, soft=1.5)
            cv.ink([(c, True, 2.8)], key=k + f"col{i}")
        for sgn in (-1, 1):
            half = [(sgn * 54, 6), (sgn * 122, 22), (sgn * 162, 64), (sgn * 170, 140), (sgn * 150, 320), (sgn * 156, 450), (sgn * 140, 568), (sgn * 2, 568),
                    (sgn * 2, 200), (sgn * 36, 100), (sgn * 60, 34)]
            poly = T(spline(half, True, 6))
            cv.fill(poly, NAVY, dens=0.88, color2=NAVY2, key=k + f"bz{sgn}", anchor=F.neck)
            if sgn == -ch.dir:
                cv.hatch(poly, angle=60, spacing=4.5, alpha=0.4, key=k + f"bzh{sgn}", fade=((-ch.dir, 0.4), 0.2, 1.0))
            cv.ink([(poly, True)], 3.4, key=k + f"bz{sgn}")
            cv.ink([(T(spline([(sgn * 54, 10), (sgn * 82, 74), (sgn * 64, 88), (sgn * 12, 196)])), False, 2.6)],
                   key=k + f"lp{sgn}")
        sq = T([(-118, 150), (-92, 150), (-100, 132), (-108, 128)])
        cv.fill(sq, (0.85, 0.3, 0.32), dens=0.8, key=k + "sq", soft=1.5, anchor=F.neck)
        cv.ink([(T([(-126, 152), (-84, 152)]), False, 2.4)], key=k + "pk")


def eye(cv, ch, p, T, ex, ey, sx, k):
    lx, ly = p.look
    if p.happy > 0.5:
        cv.ink([(T(spline([(ex - 15 * sx, ey + 5), (ex, ey - 9), (ex + 15 * sx, ey + 5)])), False, 5.0)], key=k)
        return
    o = p.open
    if o < 0.2:
        cv.ink([(T(spline([(ex - 15 * sx, ey + 1), (ex, ey + 6), (ex + 15 * sx, ey + 1)])), False, 4.2)], key=k)
        return
    rx, ry = 15.5 * sx * (0.9 + 0.1 * o), 19 * o
    white = T(ellipse(ex, ey, rx, ry, n=30))
    cv.paint(white, (0.99, 0.98, 0.95))
    px, py = ex + lx * 5 * sx, ey + ly * 6 * min(o, 1)
    pr = 9.5 if o <= 1.05 else 9.5 - (o - 1) * 10
    pup = T(ellipse(px, py, pr * sx, min(12.5, ry - 2) * (1 if o <= 1.05 else 0.85), n=24))
    cv.paint(pup, (0.17, 0.11, 0.10))
    cv.paint(T(ellipse(px - 3 * sx, py - 5, 3.2, 3.2, n=12)), (1, 1, 1))
    up = T(ellipse(ex, ey, rx, ry, n=20, a0=math.pi * 1.05, a1=math.pi * 1.95))
    lo = T(ellipse(ex, ey, rx, ry, n=16, a0=math.pi * 0.15, a1=math.pi * 0.85))
    strokes = [(up, False, 4.6), (lo, False, 2.0)]
    if ch.female:
        side = 1 if ex > p.fx else -1
        ox = ex + side * rx * 0.85
        strokes.append((T([(ox, ey - ry * 0.55), (ox + side * 9, ey - ry * 0.9)]), False, 2.6))
        strokes.append((T([(ox - side * 4, ey - ry * 0.8), (ox + side * 3, ey - ry * 1.2)]), False, 2.2))
    cv.ink(strokes, key=k)


def mouth(cv, ch, p, T, k, anchor):
    cx, cy = p.fx + 4, 74
    w, s, o = p.mw, p.smile, p.mopen
    L, R = (cx - w / 2, cy - s * 9), (cx + w / 2, cy - s * 9)
    if o > 0.07:
        up = spline([L, (cx, cy + s * 3 - o * 3), R], n=10)
        lo = spline([R, (cx + w * 0.2, cy + s * 3 + 6 + o * 30), (cx - w * 0.2, cy + s * 3 + 6 + o * 30), L], n=8)
        poly = T(np.vstack([up, lo]))
        cv.fill(poly, (0.40, 0.08, 0.11), dens=0.95, key=k + "m", soft=1.5, anchor=anchor, shift=(0, 0))
        tongue = T(ellipse(cx, cy + s * 3 + 4 + o * 30, w * 0.26, 4 + o * 8))
        cv.wash(tongue, (0.92, 0.45, 0.45), dens=0.8, knock=False, key=k + "t", soft=1.5, anchor=anchor,
                clip=[poly], shift=(0, 0))
        cv.ink([(poly, True, 3.4)], key=k + "m")
    else:
        if p.mwob > 0.5:
            pts = [L, (cx - w / 4, cy - 3), (cx, cy + 2), (cx + w / 4, cy - 3), R]
            pts = [(x, y + 3) for x, y in pts]
        else:
            pts = [L, (cx, cy + s * 4), R]
        strokes = [(T(spline(pts, n=10)), False, 4.0)]
        if s > 0.6:
            strokes.append((T([(L[0] - 3, L[1] - 3), (L[0] + 2, L[1] + 4)]), False, 2.4))
            strokes.append((T([(R[0] + 3, R[1] - 3), (R[0] - 2, R[1] + 4)]), False, 2.4))
        cv.ink(strokes, key=k + "m")


def draw_head(cv, ch, p, F, k):
    T = lambda pts: xf(pts, F.hc, F.hr, 1, ch.dir)
    a = F.hc
    ear = T(spline(EAR, False))
    cv.fill(ear, ch.skin, dens=0.6, color2=ch.skin2, key=k + "ear", anchor=a)
    cv.ink([(ear, False, 3.2), (T(spline([(-104, -4), (-114, 8), (-104, 20)])), False, 2.2)], key=k + "ear")
    if ch.female:
        ring = T(ellipse(-110, 50, 7, 9))
        cv.fill(ring, GOLD, dens=0.9, soft=1.5, key=k + "ring", anchor=a)
        cv.ink([(ring, True, 1.8)], key=k + "ring")
    head = T(spline(HEAD, True))
    cv.fill(head, ch.skin, dens=0.55, color2=ch.skin2, key=k + "hd", anchor=a)
    cv.wash(T(spline([(-104, -10), (-96, 50), (-66, 98), (-40, 70), (-70, 20)], True)), (0.85, 0.62, 0.58), dens=0.2,
            knock=False, key=k + "hsh", anchor=a, soft=9, clip=[head], hard=1.5)
    cv.hatch(head, angle=70, spacing=4.5, alpha=0.22, key=k + "hdh", fade=((-ch.dir, 0.3), 0.72, 1.0))
    if p.blush > 0.02:
        for bx in (p.fx - 40, p.fx + 46):
            cv.wash(T(ellipse(bx, 34, 22, 12)), BLUSH, dens=0.5 * p.blush, knock=False, key=k + f"bl{bx}", soft=6,
                    anchor=a, edge=0.2)
    cv.ink([(head, True)], 3.8, key=k + "hd")
    fx = p.fx
    eye(cv, ch, p, T, fx - 36, -4, 1.0, k + "e1")
    eye(cv, ch, p, T, fx + 41, -4, 0.82, k + "e2")
    brows = []
    for ex, so in ((fx - 36, -1), (fx + 41, 1)):
        by = -38 - p.raise_ * 9
        outer = (ex + so * 17, by + 3 + p.worry * 4)
        mid = (ex, by - 3 - p.worry * 2)
        inner = (ex - so * 15, by + 1 - p.worry * 13)
        brows.append((T(spline([outer, mid, inner], n=6)), False, 6.0 if not ch.female else 4.6))
    cv.ink(brows, key=k + "br", color=(0.22, 0.12, 0.10))
    cv.ink([(T(spline([(fx + 10, 8), (fx + 23, 34), (fx + 11, 43)])), False, 3.2)], key=k + "ns")
    mouth(cv, ch, p, T, k, a)
    # hair
    if ch.female:
        fh = T(spline(W_FRONTHAIR, True))
        cv.fill(fh, ch.hair, dens=0.85, color2=ch.hair2, key=k + "fh", anchor=a)
        cv.hatch(fh, angle=-30 * ch.dir, spacing=4, alpha=0.3, key=k + "fhh", fade=((-ch.dir, -0.6), 0.3, 1.0))
        cv.ink([(fh, True)], 3.6, key=k + "fh")
        cv.ink([(T(spline([(-70, -110), (-30, -122), (20, -118)])), False, 2.0),
                (T(spline([(40, -110), (80, -82), (100, -40)])), False, 2.0),
                (T(spline([(-96, -60), (-90, -20), (-80, 4)])), False, 2.0)], key=k + "fhs", alpha=0.6)
    else:
        hh = T(spline(M_HAIR, True))
        cv.fill(hh, ch.hair, dens=0.9, color2=ch.hair2, key=k + "hh", anchor=a)
        cv.hatch(hh, angle=-30 * ch.dir, spacing=4, alpha=0.35, key=k + "hhh", fade=((-ch.dir, -0.6), 0.2, 1.0))
        cv.ink([(hh, True)], 3.6, key=k + "hh")
        cv.ink([(T(spline([(-40, -128), (10, -138), (60, -126)])), False, 2.0),
                (T(spline([(-74, -96), (-40, -100), (0, -96)])), False, 2.0)], key=k + "hhs", alpha=0.6)
    if p.sweat is not None and 0 <= p.sweat <= 1.6:
        s = min(p.sweat, 1.0)
        dx, dy = (fx + 84, -70 + s * 50)
        drop = T(spline([(dx, dy - 22), (dx + 9, dy - 2), (dx + 6, dy + 8), (dx - 6, dy + 8), (dx - 9, dy - 2)], True))
        cv.paint(drop, (0.97, 0.98, 1.0))
        cv.wash(drop, (0.55, 0.75, 0.95), dens=0.6, knock=False, key=k + "sw", soft=1.5, anchor=a)
        cv.ink([(drop, True, 2.6)], key=k + "sw")


def ik(S, Hn, pref, Lmax=205):
    S, Hn = np.asarray(S, float), np.asarray(Hn, float)
    v = Hn - S
    d = float(np.hypot(*v)) + 1e-6
    L = min(Lmax, max(d * 0.56, 60))
    if d >= 2 * L:
        return S + v / 2
    h = math.sqrt(L * L - (d / 2) ** 2)
    m = S + v / 2
    n = np.array([-v[1], v[0]]) / d
    e1, e2 = m + n * h, m - n * h
    pref = np.asarray(pref, float)
    return e1 if (e1 - m) @ pref > (e2 - m) @ pref else e2


def tube(center, w0, w1):
    c = np.asarray(center, float)
    tg = np.gradient(c, axis=0)
    tg /= np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-9
    n = np.stack([-tg[:, 1], tg[:, 0]], 1)
    w = np.linspace(w0, w1, len(c))[:, None] / 2
    return c + n * w, c - n * w


def hand(cv, ch, Hp, u, mode, k, skin):
    u = np.asarray(u, float)
    v = np.array([-u[1], u[0]])
    if v[1] > 0:
        v = -v
    M = lambda pts: np.array([Hp + x * u + y * v for x, y in pts])
    if mode in ("grip", "phone"):
        shape = [(-24, -16), (-6, -21), (14, -21), (27, -12), (31, 2), (25, 17), (8, 22), (-12, 20), (-26, 10)]
        lines = [[(10, -18), (16, -4)], [(17, -8), (22, 6)], [(-6, 14), (8, 25), (22, 20)]]
    else:
        shape = [(-24, -15), (6, -18), (30, -14), (44, -5), (45, 6), (31, 12), (6, 15), (-24, 13)]
        lines = [[(22, -9), (42, -3)], [(22, 2), (42, 4)], [(-2, 13), (16, 22), (28, 19)]]
    poly = M(spline(shape, True, 5))
    cv.fill(poly, skin[0], dens=0.6, color2=skin[1], key=k + "hand", anchor=Hp)
    cv.ink([(poly, True, 3.2)] + [(M(spline(l, n=5)), False, 2.2) for l in lines], key=k + "hand")


def arm(cv, ch, S, Hp, pref, k, mode="grip"):
    E = ik(S, Hp, pref)
    Hp = np.asarray(Hp, float)
    u = Hp - E
    u /= np.hypot(*u) + 1e-9
    wrist = Hp - u * 20
    c = spline([S, E, wrist], n=12)
    if ch.female:
        l, r = tube(c, 50, 36)
        poly = np.vstack([l, r[::-1]])
        cv.fill(poly, ch.skin, dens=0.55, color2=ch.skin2, key=k + "arm", anchor=E)
        cv.ink([(l, False, 3.4), (r, False, 3.4)], key=k + "arm")
    else:
        l, r = tube(c, 66, 52)
        poly = np.vstack([l, r[::-1]])
        cv.fill(poly, NAVY, dens=0.88, color2=NAVY2, key=k + "arm", anchor=E)
        cv.ink([(l, False, 3.4), (r, False, 3.4)], key=k + "arm")
        cuff_c = np.array([wrist - u * 14, wrist + u * 4])
        cl, cr = tube(cuff_c, 46, 44)
        cuff = np.vstack([cl, cr[::-1]])
        cv.fill(cuff, SHIRT, dens=0.4, key=k + "cuff", anchor=E, soft=1.5)
        cv.ink([(cuff, True, 2.6)], key=k + "cuff")
    return u


# ---------------------------------------------------------------- props
GLASS_BOWL = [(-36, -150), (-41, -112), (-30, -74), (-9, -60), (0, -59), (9, -60), (30, -74), (41, -112), (36, -150)]


def glass(cv, origin, tilt, k, level=-104, sc=0.85, slosh=0.0):
    T = lambda pts: xf(pts, origin, tilt, sc)
    bowl = T(spline(GLASS_BOWL, n=8))
    surf_pt = T([(0, level)])[0]
    ang = slosh
    wine = clip_halfplane(bowl, surf_pt, (math.sin(ang), math.cos(ang)))
    cv.wash(bowl, (0.86, 0.9, 0.94), dens=0.18, key=k + "gb", soft=2, anchor=origin, knock=False)
    if wine is not None:
        cv.fill(wine, WINE, dens=0.92, color2=WINE2, key=k + "wn", soft=1.5, anchor=origin, shift=(0.5, 0.5))
        top = wine[np.argsort(wine[:, 1])[:2]]
    stem = T(rrect(-3.5, -60, 3.5, 40, 3))
    foot = T(ellipse(0, 40, 33, 7))
    cv.fill(foot, (0.86, 0.9, 0.94), dens=0.2, key=k + "gf", soft=1.5, anchor=origin)
    cv.fill(stem, (0.86, 0.9, 0.94), dens=0.2, key=k + "gs", soft=1, anchor=origin)
    cv.ink([(bowl, False, 2.6), (T(ellipse(0, -150, 36, 6)), True, 1.8), (stem, True, 1.8), (foot, True, 2.2)],
           key=k + "g")
    cv.pstroke(T(spline([(-30, -138), (-34, -112), (-26, -86)])), 4.5, (1, 1, 1), 0.85, key=k + "hl")


def candle(cv, i, k):
    holder = ellipse(540, 1398, 46, 11)
    cv.fill(holder, GOLD, dens=0.8, key=k + "ch", soft=2)
    cv.ink([(holder, True, 2.6)], key=k + "ch")
    body = rrect(526, 1290, 554, 1398, 5)
    cv.fill(body, (0.97, 0.93, 0.82), dens=0.25, key=k + "cb", soft=2)
    cv.ink([(body, True, 2.6)], key=k + "cb")
    rng = np.random.default_rng(i * 7 + 3)
    fh = 46 + rng.uniform(-7, 7)
    sw = rng.uniform(-5, 5)
    flame = spline([(540, 1290), (553, 1272), (540 + sw, 1290 - fh), (527, 1272)], True, 8)
    cv.paint(flame, (1.0, 0.93, 0.6))
    cv.wash(flame, (1.0, 0.62, 0.2), dens=0.55, knock=False, key=k + "fl", soft=1.5, edge=1.4)
    cv.ink([(flame, True, 2.0)], color=(0.6, 0.3, 0.1), key=k + "fl")
    cv.ink([([(540, 1291), (540, 1280)], False, 2.2)], key=k + "wk")
    return fh


def vase(cv, k):
    stem = spline([(470, 1340), (466, 1270), (472, 1205)], n=6)
    cv.ink([(stem, False, 3.2)], color=(0.25, 0.45, 0.2), key=k + "rs")
    leaf = spline([(468, 1262), (444, 1240), (430, 1250), (448, 1262)], True)
    cv.fill(leaf, (0.35, 0.6, 0.3), dens=0.8, key=k + "lf", soft=1.5)
    cv.ink([(leaf, True, 2.0)], key=k + "lf")
    rose = spline([(472, 1170), (494, 1182), (494, 1206), (472, 1218), (452, 1206), (452, 1182)], True)
    cv.fill(rose, (0.82, 0.12, 0.2), dens=0.88, color2=(0.9, 0.25, 0.3), key=k + "ro", soft=1.5)
    cv.ink([(rose, True, 2.6), (spline([(462, 1190), (474, 1182), (484, 1194), (472, 1204), (466, 1194)]), False, 2.0)],
           key=k + "ro")
    v = spline([(458, 1300), (452, 1340), (446, 1380), (470, 1400), (494, 1380), (488, 1340), (482, 1300)], n=6)
    v = np.vstack([v, [(458, 1300)]])
    cv.fill(v, (0.6, 0.78, 0.86), dens=0.35, key=k + "vs", soft=1.5)
    cv.ink([(v, True, 2.4)], key=k + "vs")


def phone_table(cv, pos, lit, facedown, k, shake=(0, 0)):
    T = lambda pts: xf(xf(pts, (0, 0), 1.25) * (1, 0.5), (pos[0] + shake[0], pos[1] + shake[1]))
    body = T(rrect(-36, -66, 36, 66, 12))
    cv.fill(body, (0.17, 0.17, 0.22), dens=0.95, key=k + "pb", soft=1.5)
    if not facedown:
        scr = T(rrect(-30, -59, 30, 59, 8))
        if lit:
            cv.paint(scr, (0.80, 0.90, 1.0))
            cv.wash(scr, (0.55, 0.65, 0.95), dens=0.35, knock=False, key=k + "ps", soft=2)
            cv.paint(T(rrect(-25, -30, 25, -6, 5)), (1, 1, 1), 0.9)
        else:
            cv.fill(scr, (0.12, 0.14, 0.22), dens=0.9, key=k + "ps", soft=1.5)
    else:
        cv.paint(T(ellipse(-18, -44, 8, 8)), (0.35, 0.35, 0.4))
    cv.ink([(body, True, 2.6)], key=k + "pb")


def phone_in_hand(cv, Hp, k):
    body = rrect(Hp[0] - 34, Hp[1] - 105, Hp[0] + 34, Hp[1] + 20, 12)
    cv.fill(body, (0.22, 0.22, 0.27), dens=0.95, key=k + "ph", soft=1.5)
    cam = rrect(Hp[0] - 26, Hp[1] - 96, Hp[0] - 2, Hp[1] - 64, 7)
    cv.fill(cam, (0.32, 0.32, 0.38), dens=0.9, key=k + "pc", soft=1)
    cv.ink([(body, True, 2.8), (cam, True, 2.0)], key=k + "ph")
    cv.pstroke([(Hp[0] + 26, Hp[1] - 95), (Hp[0] + 26, Hp[1] - 20)], 3, (0.6, 0.6, 0.7), 0.6, key=k + "phl")


def buzz_lines(cv, pos, i, k):
    x, y = pos
    a = 1 if i % 2 == 0 else -1
    strokes = []
    for s in (-1, 1):
        for r in (64, 84):
            pts = ellipse(x, y, r, r * 0.55, n=8, a0=(-0.45 if s > 0 else math.pi - 0.45), a1=(0.45 if s > 0 else math.pi + 0.45))
            strokes.append((pts + (0, a * 2), False, 3.0))
    cv.ink(strokes, key=k + "bz", color=(0.3, 0.2, 0.2))


def sparkle(cv, c, u, k):
    x, y = c
    r1, r2 = 26 + 40 * u, 60 + 70 * u
    star = []
    for j in range(8):
        a = j * math.pi / 4
        r = r2 * 0.75 if j % 2 == 0 else r2 * 0.35
        star.append((x + r * math.cos(a), y + r * math.sin(a)))
    star = spline(star, True, 3)
    cv.wash(star, (1.0, 0.86, 0.4), dens=0.6 * (1 - u * 0.6), knock=False, key=k + "sp", soft=2)
    lines = []
    for j in range(8):
        a = j * math.pi / 4 + math.pi / 8
        lines.append(([(x + r1 * math.cos(a), y + r1 * math.sin(a)), (x + r2 * math.cos(a), y + r2 * math.sin(a))], False, 3.6))
    cv.ink(lines, key=k + "spl", color=(0.55, 0.35, 0.1))


def heart(cv, c, s, k):
    x, y = c
    pts = spline([(0, -10), (14, -24), (30, -18), (30, 0), (0, 28), (-30, 0), (-30, -18), (-14, -24)], True)
    poly = pts * s + (x, y)
    cv.fill(poly, (0.92, 0.3, 0.4), dens=0.75, key=k + "ht", soft=1.5)
    cv.ink([(poly, True, 2.6)], key=k + "ht")


# ---------------------------------------------------------------- sets
TAB_S, TAB_O = 0.48, (540 - 0.48 * 540, 1115 - 0.48 * 1400)


def tab_cam(cam):
    cx, cy, z = cam
    return ((cx - TAB_O[0]) / TAB_S, (cy - TAB_O[1]) / TAB_S, TAB_S * z)


def tab2world(p):
    return (p[0] * TAB_S + TAB_O[0], p[1] * TAB_S + TAB_O[1])


TABLE = (390.0, 390.0, 95.0, 130.0)   # iso x, y, top height, radius
CLOTH, CLOTH2 = (0.94, 0.90, 0.83), (0.90, 0.86, 0.84)


def draw_iso_table(cv):
    x, y, zt, r = TABLE
    top = iso.circ3(x, y, r, zt, 72)
    a = np.linspace(-math.pi / 4, 3 * math.pi / 4, 40)
    upper = iso.PA([(x + r * math.cos(t), y + r * math.sin(t), zt) for t in a])
    lower = iso.PA([(x + (r + 7) * math.cos(t), y + (r + 7) * math.sin(t), 8 + 3 * math.sin(t * 14)) for t in a[::-1]])
    drop = np.vstack([upper, lower])
    cv.gouache(drop, CLOTH, color2=CLOTH2, key="tbdrop", shade_dir=(0, 1), shade=0.3, boil=True, jit=0.5)
    for side in (-1, 1):
        ang = -math.pi / 4 if side > 0 else 3 * math.pi / 4
        e = iso.PA([(x + r * math.cos(ang + side * -0.55), y + r * math.sin(ang + side * -0.55), zt),
                    (x + r * math.cos(ang), y + r * math.sin(ang), zt),
                    (x + (r + 7) * math.cos(ang), y + (r + 7) * math.sin(ang), 8),
                    (x + (r + 7) * math.cos(ang + side * -0.55), y + (r + 7) * math.sin(ang + side * -0.55), 8)])
        cv.wash(e, (0.55, 0.50, 0.62), dens=0.45, soft=10, key=f"tbsh{side}", hard=1.2, clip=[drop])
    cv.hatch(drop, angle=90, spacing=6, alpha=0.35, key="tbh", fade=((1, 0), 0.6, 1.0))
    cv.hatch(drop, angle=90, spacing=6, alpha=0.35, key="tbh2", fade=((-1, 0), 0.6, 1.0))
    folds = []
    for t in np.linspace(-0.6, 2.2, 9):
        p0 = iso.P(x + r * math.cos(t), y + r * math.sin(t), zt - 6)
        p1 = iso.P(x + (r + 7) * math.cos(t + 0.04), y + (r + 7) * math.sin(t + 0.04), 14)
        folds.append((spline([p0, ((p0[0] + p1[0]) / 2 + 3, (p0[1] + p1[1]) / 2), p1]), False, 0.9))
    cv.gouache(top, CLOTH, key="tbtop", shade_dir=(0, 1), shade=0.12, jit=0.5)
    cv.ink([(top, True, 1.5), (drop, True, 1.5)] + folds, key="tbl")


def draw_restaurant(cv, t, i, cam):
    pw, pm = pose_w(t), pose_m(t)
    Fw, Fm = WOMAN.frame(pw), MAN.frame(pm)
    cv.set_cam(cam)
    for (x, y, f) in ((317, 463, (0.707, -0.707)), (463, 317, (-0.707, 0.707))):
        cv.shadow(iso.circ3(x - 6, y + 6, 46, 0), 0.5, 6)
        iso.chair_iso(cv, x, y, f"ch{x}", facing=f, col=(0.36, 0.21, 0.13))
    cv.shadow(iso.circ3(TABLE[0] + 14, TABLE[1] + 14, TABLE[3] + 14, 0), 0.55, 9)
    cv.set_cam(tab_cam(cam))
    for ch, p, F in ((WOMAN, pw, Fw), (MAN, pm, Fm)):
        k = ch.name
        cv.shade_dir = (-ch.dir, 0.5)
        draw_back_hair(cv, ch, p, F, k)
        draw_torso(cv, ch, p, F, k)
        draw_head(cv, ch, p, F, k)
    cv.set_cam(cam)
    draw_iso_table(cv)
    cv.set_cam(tab_cam(cam))
    cv.shade_dir = (0, 1)
    vase(cv, "vs")
    fh = candle(cv, i, "cd")
    phone_pos = (742, 1452)
    buzzing = in_any(t, BUZZ)
    if not pm.phone:
        sh = ((4 if i % 2 else -4), 0) if buzzing else (0, 0)
        phone_table(cv, phone_pos, lit=(3.3 <= t < 6.3), facedown=(t >= 11.0), k="pt", shake=sh)
    for ch, p, F in ((WOMAN, pw, Fw), (MAN, pm, Fm)):
        k = ch.name
        cv.shade_dir = (-ch.dir, 0.5)
        sk = (ch.skin, ch.skin2)

        def do_b():
            uB = arm(cv, ch, F.shB, p.handB, (-ch.dir, 0.5), k + "B", p.modeB)
            if p.phone:
                phone_in_hand(cv, p.handB, k + "P")
            hand(cv, ch, p.handB, uB, "grip" if p.phone else p.modeB, k + "B", sk)

        if not p.phone:
            do_b()
        uA = arm(cv, ch, F.shA, p.handA, (-ch.dir * 0.5, 1.0), k + "A")
        slosh = -ch.dir * p.gtilt * D2R * 0.7
        glass(cv, p.handA, ch.dir * p.gtilt * D2R, k + "G", slosh=slosh)
        hand(cv, ch, p.handA, uA, "grip", k + "A", sk)
        if p.phone:
            do_b()
    if buzzing and not pm.phone:
        buzz_lines(cv, phone_pos, i, "bz")
    if 12.5 <= t < 12.95:
        sparkle(cv, (540, 872), (t - 12.5) / 0.45, "spk")
    for j, (t0, x0, x1) in enumerate(((13.4, 540, 515), (13.75, 560, 590), (14.1, 520, 540))):
        if t >= t0:
            u = min((t - t0) / 1.5, 1.2)
            y = 980 - u * 330
            x = x0 + (x1 - x0) * u + 12 * math.sin(u * 7 + j)
            heart(cv, (x, y), 0.55 + 0.5 * min(u * 2, 1), f"h{j}")
    # light passes (in tableau coords)
    flame = (540, 1290 - fh * 0.5)
    cv.light(flame, 170, WARM, 0.22)
    cv.light(flame, 45, (1, 0.9, 0.6), 0.45)
    if 3.3 <= t < 6.3 and not pm.phone:
        cv.light(phone_pos, 80, (0.7, 0.85, 1.0), 0.4)
    if pm.phone:
        cv.light((pm.handB[0] - 30, pm.handB[1] - 120), 130, (0.7, 0.85, 1.0), 0.28)
    # lamp light cone (world)
    cv.set_cam(cam)
    lx, ly = iso.P(390, 390, iso.LAMP_Z)
    cone = np.array([(lx - 52, ly + 4), (lx + 52, ly + 4), (lx + 175, 1150), (lx - 175, 1150)], float)
    cv.glow_poly(cone, (1.0, 0.82, 0.5), 0.13, soft=22)


# ---------------------------------------------------------------- phone close-up
PC = np.array([540.0, 880.0])


def closeup_light(x, y):
    out = np.empty(np.broadcast(x, y).shape + (3,), np.float32)
    out[:] = np.array([0.80, 0.70, 0.72], np.float32)
    d = ((x - 540) / 380.0) ** 2 + ((y - 760) / 520.0) ** 2
    out += np.exp(-d)[..., None] * np.array([0.30, 0.38, 0.55], np.float32)
    d2 = ((x - 980) / 500.0) ** 2 + ((y - 200) / 600.0) ** 2
    out += np.exp(-d2)[..., None] * np.array([0.45, 0.30, 0.15], np.float32)
    return out


def draw_closeup_bg(cv):
    k = "cbg"
    cv.gouache(rrect(-200, -200, 1280, 2100, 10), (0.30, 0.19, 0.17), color2=(0.38, 0.22, 0.18), key=k + "base",
               shade_dir=(0, 1), shade=0.35, light=False, jit=0, tex=0.05, boil=False)
    # out-of-focus room: shelves, window, her dress
    cv.wash(rrect(60, 120, 420, 520, 30), (0.20, 0.24, 0.42), dens=0.6, soft=40, hard=1.0, key=k + "win", boil=False)
    cv.wash(ellipse(150, 980, 300, 380), (0.16, 0.40, 0.36), dens=0.5, soft=55, hard=1.0, key=k + "dress", boil=False)
    cv.wash(rrect(-200, 1460, 1280, 2100, 10), (0.95, 0.9, 0.82), dens=0.0, soft=40, key=k + "x", boil=False)
    cv.gouache(rrect(-200, 1500, 1280, 2100, 10), (0.80, 0.72, 0.62), key=k + "cloth", light=False, shade=0.5,
               boil=False, jit=0, tex=0.03, soft=14)
    rng = np.random.default_rng(11)
    for j in range(26):
        x, y, r = rng.uniform(0, 1080), rng.uniform(0, 1450), rng.uniform(25, 85)
        c = (1.0, 0.78, 0.42) if j % 4 else (0.7, 0.8, 1.0)
        cv.wash(ellipse(x, y, r, r), (1.0, 0.85, 0.6), dens=0.0, soft=5, key=k + f"bk{j}", boil=False)
        cv.light((x, y), r * 0.7, c, rng.uniform(0.15, 0.4))
        cv.ink([(ellipse(x, y, r, r), True, 0.8)], key=k + f"bkl{j}", alpha=0.12, boil=False)
    cv.light((900, 1560), 180, WARM, 0.45)


def draw_closeup(cv, t, i):
    k = "cu"
    dt = t - 86 / 12
    off = np.array([3 * math.sin(2.1 * t), 4 * math.sin(1.7 * t + 1)])
    rot = (-3 + 0.7 * math.sin(1.3 * t)) * D2R
    c = PC + off
    T = lambda pts: xf(pts, c, rot)
    # forearms + palms behind the phone
    for s in (-1, 1):
        sl = spline([(s * 640, 1500), (s * 470, 900), (s * 300, 540)], n=10)
        sl = T(sl)
        l, r = tube(sl, 200, 170)
        sleeve = np.vstack([l, r[::-1]])
        cv.fill(sleeve, NAVY, dens=0.88, color2=NAVY2, key=k + f"sl{s}", anchor=c)
        cv.ink([(l, False, 4.4), (r, False, 4.4)], key=k + f"sl{s}")
        cuff = T(spline([(s * 230, 460), (s * 340, 400), (s * 400, 560), (s * 285, 625)], True))
        cv.fill(cuff, SHIRT, dens=0.45, key=k + f"cf{s}", anchor=c)
        cv.ink([(cuff, True, 3.6)], key=k + f"cf{s}")
        palm = T(ellipse(s * 250, 330, 100, 160, rot=s * 0.25))
        cv.fill(palm, SKIN_M, dens=0.6, color2=SKIN_M2, key=k + f"pm{s}", anchor=c)
        cv.ink([(palm, True, 4.0)], key=k + f"pm{s}")
    # phone body + screen
    body = T(rrect(-255, -520, 255, 520, 64))
    cv.fill(body, (0.18, 0.18, 0.22), dens=0.95, key=k + "body", anchor=c, soft=2)
    cv.ink([(body, True, 4.4)], key=k + "body")
    scr = T(rrect(-234, -498, 234, 498, 48))
    cv.paint(scr, (0.93, 0.92, 0.95))
    cv.wash(scr, (0.20, 0.20, 0.45), dens=0.92, color2=(0.32, 0.24, 0.52), key=k + "scr", anchor=c, knock=False,
            rough=0.3, soft=2)
    cv.wash(T(rrect(-234, 100, 234, 560, 40)), (0.85, 0.45, 0.55), dens=0.4, key=k + "scr2", anchor=c, knock=False,
            soft=45, clip=[scr])
    # wallpaper moon + stars
    mo = T(ellipse(150, 330, 46, 46))
    cv.paint(mo, (1.0, 0.95, 0.78), 0.85)
    cv.fill(T(ellipse(170, 318, 40, 40)), (0.30, 0.25, 0.52), dens=0.95, key=k + "mo2", anchor=c, soft=1.5, clip=[mo])
    rng = np.random.default_rng(3)
    for j in range(14):
        x, y = rng.uniform(-200, 200), rng.uniform(-470, 460)
        if -170 < y < 110 or abs(x - 150) < 60 and abs(y - 330) < 60:
            continue
        cv.paint(T(ellipse(x, y, 3.5, 3.5, n=8)), (1, 0.97, 0.85), 0.85)
    island = T(rrect(-62, -478, 62, -444, 17))
    cv.paint(island, (0.06, 0.06, 0.08))
    deg = rot / D2R
    def txt(s, x, y, size, col, bold=False, align="left", fam="Inter", jit=0.5):
        p = T([(x, y)])[0]
        cv.text(s, p[0], p[1], size, col, bold=bold, align=align, family=fam, rot=rot, jitter=jit)
    txt("Saturday", 0, -362, 30, (0.95, 0.94, 1.0), bold=True, align="center")
    txt("8:31", 0, -230, 150, (0.98, 0.97, 1.0), align="center", fam="Inter Display")
    # notification card pops in
    if dt >= 0.1:
        u = dt - 0.1
        sc = 0.82 if u < 0.08 else (1.05 if u < 0.17 else 1.0)
        cc = np.array([0, -32])
        S = lambda pts: T((np.asarray(pts, float) - cc) * sc + cc)
        card = S(rrect(-214, -150, 214, 86, 36))
        cv.paint(card, (0.97, 0.96, 0.93), 0.94)
        cv.ink([(card, True, 3.0)], key=k + "card")
        icon = S(rrect(-190, -128, -124, -62, 17))
        cv.fill(icon, (0.96, 0.52, 0.32), dens=0.9, color2=(0.92, 0.38, 0.42), key=k + "icon", anchor=c, soft=1.2)
        cv.ink([(icon, True, 2.4)], key=k + "icon")
        def ctxt(s, x, y, size, col, bold=False, align="left", fam="Inter"):
            p = S([(x, y)])[0]
            cv.text(s, p[0], p[1], size * sc, col, bold=bold, align=align, family=fam, rot=rot, jitter=0.35)
        ctxt("A", -157, -78, 40, (1, 1, 1), bold=True, align="center")
        ctxt("AylluOS", -106, -84, 29, (0.25, 0.22, 0.24), bold=True)
        ctxt("now", 192, -84, 25, (0.45, 0.43, 0.46), align="right")
        ctxt("Baby is Sleeping", -190, -4, 42, (0.12, 0.10, 0.12), bold=True)
        ctxt("8:31pm · Grandma", -190, 52, 34, (0.22, 0.20, 0.22))
    cv.paint(T(rrect(-80, 474, 80, 482, 4)), (0.95, 0.95, 1.0), 0.8)
    cv.pstroke(T(spline([(-236, -380), (-240, -200), (-238, 0)])), 5, (0.55, 0.55, 0.65), 0.6, key=k + "rim")
    # thumbs in front
    for s in (-1, 1):
        th = T(spline([(s * 262, 400), (s * 226, 320), (s * 178, 262), (s * 150, 250), (s * 140, 272), (s * 166, 322),
                       (s * 196, 380), (s * 222, 440)], True))
        cv.fill(th, SKIN_M, dens=0.6, color2=SKIN_M2, key=k + f"th{s}", anchor=c)
        nail = T(ellipse(s * 158, 268, 12, 16, rot=-s * 0.7))
        cv.fill(nail, (0.98, 0.85, 0.78), dens=0.4, key=k + f"nl{s}", anchor=c, soft=1)
        cv.ink([(th, True, 3.8), (nail, True, 2.0)], key=k + f"th{s}")
    cv.light(tuple(c + (0, -60)), 420, (0.65, 0.7, 1.0), 0.18)
