"""Tiny hand-drawn / watercolor rendering engine.

Everything is drawn as masks with cairo and composited with numpy:
  * wash()  - watercolor fill: organic noisy edge, pigment pooling at the
              edges, low-frequency pigment variation, paper granulation.
  * ink()   - hand-inked lines: variable pressure, tapered ends, and a
              per-drawing "boil" so every drawing is slightly different,
              like traced animation paper.
  * paint() - opaque gouache (white highlights, eye glints, text).
  * light() - soft additive glow (candle, lamps, phone screen).
"""
import math
import os
import zlib

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

W, H = 1080, 1920
N = 2048
INK = np.array([0.20, 0.13, 0.12], np.float32)
PAPER = np.array([0.965, 0.94, 0.885], np.float32)


# --------------------------------------------------------------------------
# noise textures
# --------------------------------------------------------------------------
def _noise(sigma, seed, aniso=1.0):
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((N, N))
    F = np.fft.rfft2(a)
    ky = np.fft.fftfreq(N)[:, None]
    kx = np.fft.rfftfreq(N)[None, :]
    G = np.exp(-2 * (np.pi * sigma) ** 2 * (kx ** 2 + (ky * aniso) ** 2))
    b = np.fft.irfft2(F * G, s=(N, N)).astype(np.float32)
    return b / b.std()


class Textures:
    def __init__(self, cache_dir):
        path = os.path.join(cache_dir, "noise_v3.npz")
        if os.path.exists(path):
            d = np.load(path)
            self.low, self.mid, self.fine, self.grain = d["low"], d["mid"], d["fine"], d["grain"]
        else:
            self.low = _noise(70, 1)
            self.mid = _noise(9, 2)
            self.fine = _noise(2.5, 3)
            g = 0.35 * _noise(1.0, 4) + 0.45 * _noise(2.2, 5) + 0.35 * _noise(4.0, 6, aniso=0.3)
            self.grain = (g / g.std()).astype(np.float32)
            np.savez(path, low=self.low, mid=self.mid, fine=self.fine, grain=self.grain)
        self.grain_s = sample(self.grain, 0, 0, W, H).copy()
        mott = sample(self.low, 300, 700, W, H)
        p = PAPER[None, None, :] * (1 - 0.018 * self.grain_s[..., None] - 0.015 * mott[..., None])
        self.paper = np.clip(p, 0, 1).astype(np.float32)


def sample(f, x0, y0, w, h):
    x0 = int(x0) % N
    y0 = int(y0) % N
    if x0 + w <= N and y0 + h <= N:
        return f[y0:y0 + h, x0:x0 + w]
    ys = (np.arange(h) + y0) % N
    xs = (np.arange(w) + x0) % N
    return f[np.ix_(ys, xs)]


def blur(M, sigma):
    if sigma <= 10:
        return gaussian_filter(M, sigma, truncate=2.5)
    f = int(sigma // 5)
    h, w = M.shape
    hp, wp = -(-h // f) * f, -(-w // f) * f
    P = np.pad(M, ((0, hp - h), (0, wp - w)), mode="edge")
    small = P.reshape(hp // f, f, wp // f, f).mean((1, 3))
    small = gaussian_filter(small, sigma / f, truncate=2.5)
    big = zoom(small, f, order=1)
    return big[:h, :w]


def hseed(*parts):
    return zlib.crc32(":".join(str(p) for p in parts).encode())


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def spline(pts, closed=False, n=8):
    P = np.asarray(pts, float)
    if len(P) < 3:
        return P
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(P[-2][None])
    return np.vstack(out)


def ellipse(cx, cy, rx, ry, rot=0.0, n=40, a0=0.0, a1=2 * math.pi):
    a = np.linspace(a0, a1, n, endpoint=(a1 - a0) < 2 * math.pi - 1e-6)
    x = rx * np.cos(a)
    y = ry * np.sin(a)
    c, s = math.cos(rot), math.sin(rot)
    return np.stack([cx + c * x - s * y, cy + s * x + c * y], 1)


def rrect(x0, y0, x1, y1, r, n=6):
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            ang = math.radians(a + 90 * k / n)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return np.array(pts)


def xf(pts, origin=(0, 0), rot=0.0, scale=1.0, flip=1):
    """local -> world: flip x by `flip`, scale, rotate (radians, y-down), translate."""
    p = np.asarray(pts, float).copy()
    p[:, 0] *= flip
    p *= scale
    c, s = math.cos(rot), math.sin(rot)
    x = c * p[:, 0] - s * p[:, 1]
    y = s * p[:, 0] + c * p[:, 1]
    return np.stack([x + origin[0], y + origin[1]], 1)


def resample(pts, step, closed=False):
    p = np.asarray(pts, float)
    if closed:
        p = np.vstack([p, p[:1]])
    d = np.sqrt((np.diff(p, axis=0) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(d)])
    L = s[-1]
    if L < 1e-6:
        return p[:1], np.zeros(1)
    n = max(2, int(L / step) + 1)
    ss = np.linspace(0, L, n)
    return np.stack([np.interp(ss, s, p[:, 0]), np.interp(ss, s, p[:, 1])], 1), ss


def clip_halfplane(poly, p0, normal):
    """Keep the part of polygon where dot(p - p0, normal) >= 0 (Sutherland-Hodgman)."""
    out = []
    P = np.asarray(poly, float)
    n = np.asarray(normal, float)
    d = (P - p0) @ n
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        da, db = d[i], d[(i + 1) % len(P)]
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(a + (b - a) * t)
    return np.array(out) if len(out) >= 3 else None


def stroke_poly(sp, w, closed, rng, jitter=1.2, taper=True, overshoot=0.05):
    pts, _ = resample(sp, 2.5, closed)
    if len(pts) < 2:
        return None
    if closed:
        pts = pts[:-1]
        k = rng.integers(len(pts))
        pts = np.roll(pts, -k, 0)
        extra = max(2, int(len(pts) * overshoot))
        pts = np.vstack([pts, pts[:extra]])
    seg = np.sqrt((np.diff(pts, axis=0) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    if L < 0.5:
        return None
    tg = np.gradient(pts, axis=0)
    tn = np.sqrt((tg ** 2).sum(1))[:, None] + 1e-9
    tg = tg / tn
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    ph = rng.uniform(0, 2 * math.pi, 4)
    off = jitter * (0.55 * np.sin(s / 21.0 + ph[0]) + 0.35 * np.sin(s / 8.3 + ph[1]))
    pts = pts + nrm * off[:, None] + rng.normal(0, jitter * 0.45, 2)
    press = 0.72 + 0.28 * np.sin(s / 37.0 + ph[2]) * np.sin(s / 13.0 + ph[3])
    if taper:
        Lt = min(16.0 * max(w / 3.0, 1.0), L * 0.4)
        tp = np.clip(np.minimum(s, L - s) / max(Lt, 1e-3), 0, 1) ** 0.6
        tp = 0.22 + 0.78 * tp
    else:
        tp = 1.0
    hw = (w * press * tp / 2.0)[:, None]
    left = pts + nrm * hw
    right = pts - nrm * hw
    return np.vstack([left, right[::-1]])


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------
class Canvas:
    def __init__(self, tex, cam=(540, 960, 1.0), boil=0, base=None):
        self.tex = tex
        self.paper = tex.paper
        self.grain = tex.grain_s
        self.img = (base if base is not None else tex.paper).copy()
        self.cx, self.cy, self.z = cam
        self.boil = boil

    # ---- transforms
    def S(self, pts):
        p = np.asarray(pts, float)
        return (p - (self.cx, self.cy)) * self.z + (W / 2, H / 2)

    def S1(self, x, y):
        return ((x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + H / 2)

    # ---- masks
    def _bbox(self, polys, pad):
        polys = [p for p in polys if p is not None and len(p) > 1]
        if not polys:
            return None
        a = np.concatenate(polys)
        x0 = max(0, int(math.floor(a[:, 0].min() - pad)))
        y0 = max(0, int(math.floor(a[:, 1].min() - pad)))
        x1 = min(W, int(math.ceil(a[:, 0].max() + pad)))
        y1 = min(H, int(math.ceil(a[:, 1].max() + pad)))
        if x1 - x0 < 2 or y1 - y0 < 2:
            return None
        return x0, y0, x1, y1

    def _mask(self, polys, bb, evenodd=False):
        x0, y0, x1, y1 = bb
        w, h = x1 - x0, y1 - y0
        surf = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
        ctx = cairo.Context(surf)
        ctx.translate(-x0, -y0)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD if evenodd else cairo.FILL_RULE_WINDING)
        for p in polys:
            if p is None or len(p) < 3:
                continue
            ctx.move_to(*p[0])
            for x, y in p[1:]:
                ctx.line_to(x, y)
            ctx.close_path()
        ctx.fill()
        surf.flush()
        a = np.ndarray(shape=(h, surf.get_stride()), dtype=np.uint8, buffer=surf.get_data())[:, :w]
        return a.astype(np.float32) * (1.0 / 255.0)

    # ---- watercolor wash
    def wash(self, polys, color, dens=0.8, color2=None, edge=0.9, rough=1.0, soft=3.0,
             shift=(1.5, 2.0), knock=True, key="", anchor=(0, 0), gran=1.0, var=0.35,
             evenodd=False, boil=True, clip=None, hard=3.0):
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys if p is not None]
        z = self.z
        sg = max(1.0, soft * z)
        pad = int(sg * 3 + 10 + abs(shift[0]) * z + abs(shift[1]) * z)
        bb = self._bbox(sp, pad)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        h, w = y1 - y0, x1 - x0
        M = self._mask(sp, bb, evenodd)
        if clip is not None:
            M *= self._mask([self.S(p) for p in clip], bb)
        reg = self.img[y0:y1, x0:x1]
        if knock:
            Mk = M[..., None]
            reg *= (1 - Mk)
            reg += self.paper[y0:y1, x0:x1] * Mk
        sx, sy = int(round(shift[0] * z)), int(round(shift[1] * z))
        if sx or sy:
            Ms = np.zeros_like(M)
            hs, ws = M.shape
            Ms[max(sy, 0):hs + min(sy, 0), max(sx, 0):ws + min(sx, 0)] = \
                M[max(-sy, 0):hs - max(sy, 0), max(-sx, 0):ws - max(sx, 0)]
        else:
            Ms = M
        Sm = blur(Ms, sg)
        ax, ay = self.S1(*anchor)
        k = hseed(key)
        b = (self.boil % 3) * 37 if boil else 0
        bx = int(x0 - ax + (k % 1700) + b)
        by = int(y0 - ay + ((k // 1700) % 1700) + b)
        nm = sample(self.tex.mid, bx, by, w, h)
        nf = sample(self.tex.fine, bx, by, w, h)
        eb = np.clip(4.4 * Sm * (1 - Sm), 0, 1)
        Wm = np.clip((Sm - 0.5 + rough * eb * (0.2 * nm + 0.07 * nf)) * hard + 0.5, 0, 1)
        Wm *= M if clip is not None else 1.0
        E = np.clip(Wm - gaussian_filter(Wm, 3.5 * z + 1, truncate=2.5), 0, 1)
        nl = sample(self.tex.low, bx + 500, by + 300, w, h)
        g = self.grain[y0:y1, x0:x1]
        D = Wm * dens * (1 + var * 0.5 * np.clip(nl, -2, 2)) + E * edge * dens * 1.6
        D *= (1 + gran * 0.07 * g)
        D = np.clip(D, 0, 1.05)
        col = np.asarray(color, np.float32)
        if color2 is not None:
            t = np.clip(0.5 + 0.4 * sample(self.tex.low, bx + 900, by + 1100, w, h), 0, 1)[..., None]
            col = col * (1 - t) + np.asarray(color2, np.float32) * t
        reg *= (1 - D[..., None] * (1 - col))
        np.clip(reg, 0, 1, out=reg)

    # ---- ink lines
    def ink(self, strokes, width=3.0, color=INK, alpha=0.93, key="", jitter=1.1, boil=True):
        """strokes: list of (pts, closed) or (pts, closed, width)."""
        polys = []
        z = self.z
        for i, st in enumerate(strokes):
            pts, closed = st[0], st[1]
            w = st[2] if len(st) > 2 else width
            if pts is None or len(pts) < 2:
                continue
            seed = hseed(key, i, self.boil if boil else 0)
            rng = np.random.default_rng(seed)
            p = stroke_poly(self.S(pts), w * z, closed, rng, jitter=jitter * min(z, 1.6))
            if p is not None:
                polys.append(p)
        bb = self._bbox(polys, 4)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = self._mask(polys, bb)
        g = self.grain[y0:y1, x0:x1]
        A = M * alpha * np.clip(0.93 + 0.07 * g, 0, 1)
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - A[..., None] * (1 - np.asarray(color, np.float32)))

    # ---- opaque paint
    def paint(self, polys, color, alpha=1.0, soft=0.0, evenodd=False):
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys if p is not None]
        sg = soft * self.z
        bb = self._bbox(sp, int(sg * 3 + 3))
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = self._mask(sp, bb, evenodd)
        if sg > 0.3:
            M = gaussian_filter(M, sg)
        M = (M * alpha)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - M)
        reg += np.asarray(color, np.float32) * M

    def pstroke(self, pts, w, color, alpha=0.9, key="", jitter=0.8):
        """opaque painted stroke (gouache highlight)"""
        rng = np.random.default_rng(hseed(key, self.boil))
        p = stroke_poly(self.S(pts), w * self.z, False, rng, jitter=jitter)
        if p is None:
            return
        bb = self._bbox([p], 3)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = (self._mask([p], bb) * alpha)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - M)
        reg += np.asarray(color, np.float32) * M

    def paper_fill(self, polys):
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys]
        bb = self._bbox(sp, 2)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = self._mask(sp, bb)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - M)
        reg += self.paper[y0:y1, x0:x1] * M

    # ---- glow
    def light(self, c, r, color, strength=0.5):
        sx, sy = self.S1(*c)
        rr = r * self.z
        x0, y0 = max(0, int(sx - 2.6 * rr)), max(0, int(sy - 2.6 * rr))
        x1, y1 = min(W, int(sx + 2.6 * rr)), min(H, int(sy + 2.6 * rr))
        if x1 - x0 < 2 or y1 - y0 < 2:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        g = strength * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * rr * rr))
        reg = self.img[y0:y1, x0:x1]
        gc = g[..., None] * np.asarray(color, np.float32)
        reg[:] = 1 - (1 - reg) * (1 - gc)

    # ---- text (screen-crisp but slightly boiled)
    def text(self, s, x, y, size, color, bold=False, family="Inter", align="left", alpha=1.0,
             rot=0.0, jitter=0.6):
        rng = np.random.default_rng(hseed("txt", s, self.boil))
        sx, sy = self.S1(x, y)
        sx += rng.normal(0, jitter)
        sy += rng.normal(0, jitter)
        fs = size * self.z
        surf = cairo.ImageSurface(cairo.FORMAT_A8, W, H)
        ctx = cairo.Context(surf)
        ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(fs)
        ext = ctx.text_extents(s)
        ctx.translate(sx, sy)
        ctx.rotate(rot)
        dx = {"left": 0, "center": -ext.x_advance / 2, "right": -ext.x_advance}[align]
        ctx.move_to(dx, 0)
        ctx.show_text(s)
        surf.flush()
        M = np.ndarray(shape=(H, surf.get_stride()), dtype=np.uint8, buffer=surf.get_data())[:, :W]
        ys, xs = np.nonzero(M)
        if len(ys) == 0:
            return
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        m = (M[y0:y1, x0:x1].astype(np.float32) / 255 * alpha)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - m)
        reg += np.asarray(color, np.float32) * m

    def finish(self, vignette=0.22, flicker=0.0):
        img = self.img
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2
        v = 1 - vignette * np.clip(d, 0, 1.6) ** 1.3
        out = img * v[..., None] * (1 + flicker)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
