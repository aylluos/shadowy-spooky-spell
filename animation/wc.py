"""Hand-drawn ink + gouache/watercolor rendering engine (cairo masks + numpy compositing).

Primitives
  gouache() - opaque painted fill: brush-streak texture, value gradient, lighting,
              wobbly edges that change on every drawing.
  wash()    - transparent watercolor glaze (shadows, blush, light stains).
  ink()     - sketchy pen lines: broken into short tapered strokes, double-pass,
              pressure variation and per-drawing boil.
  hatch()   - pen hatching / cross-hatching clipped to a shape, with fade.
  paint()   - flat opaque paint (highlights, text plates).
  light()   - additive glow.
"""
import math
import os
import zlib

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

W, H = 1080, 1920
N = 2048
INK = np.array([0.13, 0.09, 0.08], np.float32)
PAPER = np.array([0.95, 0.92, 0.86], np.float32)


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
        path = os.path.join(cache_dir, "noise_v5.npz")
        if os.path.exists(path):
            d = np.load(path)
            for k in d.files:
                setattr(self, k, d[k])
        else:
            self.low = _noise(70, 1)
            self.mid = _noise(9, 2)
            self.fine = _noise(2.5, 3)
            g = 0.35 * _noise(1.0, 4) + 0.45 * _noise(2.2, 5) + 0.35 * _noise(4.0, 6, aniso=0.3)
            self.grain = (g / g.std()).astype(np.float32)
            b = 0.6 * _noise(1.4, 7, aniso=3.0) + 0.6 * _noise(4.0, 8, aniso=2.0) + 0.5 * _noise(14, 9)
            self.brush = (b / b.std()).astype(np.float32)
            np.savez(path, low=self.low, mid=self.mid, fine=self.fine, grain=self.grain, brush=self.brush)


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


def _normals(pts):
    tg = np.gradient(pts, axis=0)
    tg = tg / (np.sqrt((tg ** 2).sum(1))[:, None] + 1e-9)
    return np.stack([-tg[:, 1], tg[:, 0]], 1)


def wobble_poly(p, amp, rng):
    pts, s = resample(p, 4.0, True)
    pts = pts[:-1]
    s = s[:-1]
    if len(pts) < 3:
        return p
    nrm = _normals(pts)
    ph = rng.uniform(0, 2 * math.pi, 2)
    off = amp * (0.6 * np.sin(s / 19.0 + ph[0]) + 0.4 * np.sin(s / 7.0 + ph[1]))
    return pts + nrm * off[:, None]


def stroke_poly(sp, w, closed, rng, jitter=1.2, taper=True, overshoot=0.05, step=2.0):
    pts, _ = resample(sp, step, closed)
    if len(pts) < 2:
        return None
    if closed:
        pts = pts[:-1]
        k = rng.integers(len(pts))
        pts = np.roll(pts, -k, 0)
        extra = max(2, int(len(pts) * overshoot))
        pts = np.vstack([pts, pts[:extra]])
    return _stroke(pts, w, rng, jitter, taper)


def _stroke(pts, w, rng, jitter, taper=True):
    seg = np.sqrt((np.diff(pts, axis=0) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    if L < 0.5 or len(pts) < 2:
        return None
    nrm = _normals(pts)
    ph = rng.uniform(0, 2 * math.pi, 4)
    off = jitter * (0.55 * np.sin(s / 21.0 + ph[0]) + 0.35 * np.sin(s / 8.3 + ph[1]))
    pts = pts + nrm * off[:, None] + rng.normal(0, jitter * 0.4, 2)
    press = 0.7 + 0.3 * np.sin(s / 37.0 + ph[2]) * np.sin(s / 13.0 + ph[3])
    if taper:
        Lt = min(12.0 * max(w / 2.5, 1.0), L * 0.45)
        tp = np.clip(np.minimum(s, L - s) / max(Lt, 1e-3), 0, 1) ** 0.6
        tp = 0.15 + 0.85 * tp
    else:
        tp = 1.0
    hw = (w * press * tp / 2.0)[:, None]
    return np.vstack([pts + nrm * hw, (pts - nrm * hw)[::-1]])


def sketch_strokes(sp, w, closed, rng, jitter, broken=True):
    """split a path into several overlapping/broken tapered pen strokes"""
    pts, _ = resample(sp, 2.0, closed)
    if len(pts) < 2:
        return []
    if closed:
        pts = pts[:-1]
        pts = np.roll(pts, -rng.integers(len(pts)), 0)
        pts = np.vstack([pts, pts[:max(2, len(pts) // 25)]])
    n = len(pts)
    out = []
    i = 0
    while i < n - 1:
        ln = int(rng.uniform(28, 85)) if broken else n
        j = min(n, i + ln)
        if n - j < 10:
            j = n
        piece = pts[i:j]
        if len(piece) >= 2:
            p = _stroke(piece, w, rng, jitter)
            if p is not None:
                out.append(p)
        gap = rng.choice([-4, -3, -2, 0, 1, 2]) if broken else 0
        i = j + gap if j < n else n
    return out


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------
class Canvas:
    def __init__(self, tex, cam=(540, 960, 1.0), boil=0, base=None, size=(W, H)):
        self.tex = tex
        self.W, self.H = size
        self.grain = sample(tex.grain, 0, 0, self.W, self.H)
        self._paper = None
        if base is not None:
            self.img = base.copy()
        else:
            self.img = np.empty((self.H, self.W, 3), np.float32)
            self.img[:] = self.paper
        self.cx, self.cy, self.z = cam
        self.base_cam = cam
        self.boil = boil
        self.lightfn = None       # f(world_x, world_y) -> (h, w, 3) multiplier (base-camera world coords)

    @property
    def paper(self):
        if self._paper is None:
            mott = sample(self.tex.low, 300, 700, self.W, self.H)
            p = PAPER[None, None, :] * (1 - 0.02 * self.grain[..., None] - 0.015 * mott[..., None])
            self._paper = np.clip(p, 0, 1).astype(np.float32)
        return self._paper

    def set_cam(self, cam):
        self.cx, self.cy, self.z = cam

    # ---- transforms
    def S(self, pts):
        p = np.asarray(pts, float)
        return (p - (self.cx, self.cy)) * self.z + (self.W / 2, self.H / 2)

    def S1(self, x, y):
        return ((x - self.cx) * self.z + self.W / 2, (y - self.cy) * self.z + self.H / 2)

    def _light(self, bb):
        if self.lightfn is None:
            return None
        x0, y0, x1, y1 = bb
        cx, cy, z = self.base_cam
        xs = (np.arange(x0, x1, dtype=np.float32) - self.W / 2) / z + cx
        ys = (np.arange(y0, y1, dtype=np.float32) - self.H / 2) / z + cy
        return self.lightfn(xs[None, :], ys[:, None])

    # ---- masks
    def _bbox(self, polys, pad):
        polys = [p for p in polys if p is not None and len(p) > 1]
        if not polys:
            return None
        a = np.concatenate(polys)
        x0 = max(0, int(math.floor(a[:, 0].min() - pad)))
        y0 = max(0, int(math.floor(a[:, 1].min() - pad)))
        x1 = min(self.W, int(math.ceil(a[:, 0].max() + pad)))
        y1 = min(self.H, int(math.ceil(a[:, 1].max() + pad)))
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

    def _tex_origin(self, key, anchor, x0, y0, boil=True):
        ax, ay = self.S1(*anchor)
        k = hseed(key)
        b = (self.boil % 3) * 37 if boil else 0
        return int(x0 - ax + (k % 1700) + b), int(y0 - ay + ((k // 1700) % 1700) + b)

    # ---- gouache (opaque painted fill)
    def gouache(self, polys, color, key="", anchor=(0, 0), color2=None, shade_dir=(0.0, 1.0), shade=0.25,
                tex=0.06, light=True, edge_dark=0.12, jit=0.9, alpha=1.0, evenodd=False, clip=None, boil=True,
                soft=0.6):
        if isinstance(polys, np.ndarray):
            polys = [polys]
        rng = np.random.default_rng(hseed(key, "g", self.boil if boil else 0))
        sp = []
        for p in polys:
            if p is None or len(p) < 3:
                continue
            q = self.S(p)
            if jit > 0:
                q = wobble_poly(q, jit * min(self.z, 2.0), rng)
            sp.append(q)
        bb = self._bbox(sp, 4)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        h, w = y1 - y0, x1 - x0
        M = self._mask(sp, bb, evenodd)
        if soft > 0:
            M = gaussian_filter(M, soft)
        if clip is not None:
            M *= self._mask([self.S(p) for p in clip], bb)
        bx, by = self._tex_origin(key, anchor, x0, y0, boil)
        br = sample(self.tex.brush, bx, by, w, h)
        md = sample(self.tex.mid, bx + 300, by + 200, w, h)
        col = np.empty((h, w, 3), np.float32)
        col[:] = np.asarray(color, np.float32)
        if color2 is not None:
            t = np.clip(0.5 + 0.45 * sample(self.tex.low, bx + 900, by + 1100, w, h), 0, 1)[..., None]
            col = col * (1 - t) + np.asarray(color2, np.float32) * t
        a = np.concatenate(sp)
        dx, dy = shade_dir
        dn = math.hypot(dx, dy) + 1e-9
        dx, dy = dx / dn, dy / dn
        proj = a[:, 0] * dx + a[:, 1] * dy
        pmin, pmax = proj.min(), proj.max()
        xs = np.arange(x0, x1, dtype=np.float32)[None, :]
        ys = np.arange(y0, y1, dtype=np.float32)[:, None]
        g = np.clip(((xs * dx + ys * dy) - pmin) / max(pmax - pmin, 1.0), 0, 1)
        v = (1 - shade * g) * (1 + tex * (0.65 * br + 0.35 * md))
        col *= v[..., None]
        if edge_dark > 0:
            E = np.clip(M - gaussian_filter(M, 2.5 * min(self.z, 2.5) + 0.5, truncate=2.5), 0, 1)
            col *= (1 - edge_dark * E)[..., None]
        if light:
            L = self._light(bb)
            if L is not None:
                col *= L
        np.clip(col, 0, 1, out=col)
        A = (M * alpha)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - A)
        reg += col * A

    shade_dir = (0.0, 1.0)
    shade_amt = 0.3

    def fill(self, polys, color, dens=None, color2=None, key="", anchor=(0, 0), clip=None, evenodd=False, **kw):
        """character paint: opaque gouache lit by the scene lights"""
        self.gouache(polys, color, key=key, anchor=anchor, color2=color2, clip=clip, evenodd=evenodd,
                     shade_dir=self.shade_dir, shade=self.shade_amt, tex=0.035)

    # ---- watercolor glaze (transparent, multiplies)
    def wash(self, polys, color, dens=0.6, color2=None, edge=0.9, rough=1.0, soft=3.0,
             shift=(1.5, 2.0), knock=False, key="", anchor=(0, 0), gran=1.0, var=0.35,
             evenodd=False, boil=True, clip=None, hard=3.0, light=False):
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
        bx, by = self._tex_origin(key, anchor, x0, y0, boil)
        nm = sample(self.tex.mid, bx, by, w, h)
        nf = sample(self.tex.fine, bx, by, w, h)
        eb = np.clip(4.4 * Sm * (1 - Sm), 0, 1)
        Wm = np.clip((Sm - 0.5 + rough * eb * (0.2 * nm + 0.07 * nf)) * hard + 0.5, 0, 1)
        if clip is not None:
            Wm *= M
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
    def ink(self, strokes, width=2.4, color=INK, alpha=0.9, key="", jitter=0.9, boil=True, sketch=True,
            second=0.45, clip=None):
        """strokes: list of (pts, closed) or (pts, closed, width)."""
        polys, polys2 = [], []
        z = self.z
        zj = min(z, 2.0)
        for i, st in enumerate(strokes):
            pts, closed = st[0], st[1]
            w = st[2] if len(st) > 2 else width
            if pts is None or len(pts) < 2:
                continue
            rng = np.random.default_rng(hseed(key, i, self.boil if boil else 0))
            sp = self.S(pts)
            if sketch:
                polys += sketch_strokes(sp, w * z, closed, rng, jitter * zj)
                if second > 0 and w * z > 1.2:
                    polys2 += sketch_strokes(sp, w * z * 0.55, closed, rng, jitter * zj * 1.6)
            else:
                p = stroke_poly(sp, w * z, closed, rng, jitter=jitter * zj)
                if p is not None:
                    polys.append(p)
        cl = [self.S(p) for p in clip] if clip is not None else None
        self._ink_mask(polys, color, alpha, cl)
        if polys2:
            self._ink_mask(polys2, color, alpha * second, cl)

    def _ink_mask(self, polys, color, alpha, clip=None):
        bb = self._bbox(polys, 3)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = self._mask(polys, bb)
        if clip is not None:
            M *= self._mask(clip, bb)
        g = self.grain[y0:y1, x0:x1]
        A = M * alpha * np.clip(0.9 + 0.1 * g, 0, 1)
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - A[..., None] * (1 - np.asarray(color, np.float32)))

    # ---- hatching
    def hatch(self, polys, angle=45, spacing=7.0, width=1.1, alpha=0.55, key="", color=INK, cross=None,
              fade=None, boil=True, jitter=0.6, clip_soft=1.0, evenodd=False):
        """fade: (dir(x,y) in screen, a, b) -> weight ramps 0..1 between fractions a..b along dir."""
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys if p is not None and len(p) > 2]
        bb = self._bbox(sp, 2)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        h, w = y1 - y0, x1 - x0
        R = self._mask(sp, bb, evenodd)
        if clip_soft:
            R = gaussian_filter(R, clip_soft)
        if fade is not None:
            (fx, fy), fa, fb = fade
            n = math.hypot(fx, fy) + 1e-9
            fx, fy = fx / n, fy / n
            a = np.concatenate(sp)
            pr = a[:, 0] * fx + a[:, 1] * fy
            pmin, pmax = pr.min(), pr.max()
            xs = np.arange(x0, x1, dtype=np.float32)[None, :]
            ys = np.arange(y0, y1, dtype=np.float32)[:, None]
            gg = ((xs * fx + ys * fy) - pmin) / max(pmax - pmin, 1)
            R = R * np.clip((gg - fa) / max(fb - fa, 1e-3), 0, 1)
        sz = spacing * max(self.z, 0.6)
        angles = [angle] + ([cross] if cross is not None else [])
        lines = []
        rng = np.random.default_rng(hseed(key, "h", self.boil if boil else 0))
        cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
        rad = math.hypot(w, h) / 2 + 4
        for ang in angles:
            t = math.radians(ang)
            d = np.array([math.cos(t), math.sin(t)])
            nn = np.array([-d[1], d[0]])
            k = -rad
            while k < rad:
                c = np.array([cxm, cym]) + nn * (k + rng.normal(0, sz * 0.12))
                L = rad * rng.uniform(0.9, 1.0)
                p = np.array([c - d * L, c + d * L])
                pts = np.linspace(p[0], p[1], max(2, int(2 * L / 3)))
                s = _stroke(pts, width * min(self.z, 2.2), rng, jitter * min(self.z, 2), taper=False)
                if s is not None:
                    lines.append(s)
                k += sz
        if not lines:
            return
        M = self._mask(lines, bb)
        A = M * R * alpha
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - A[..., None] * (1 - np.asarray(color, np.float32)))

    # ---- opaque paint
    def paint(self, polys, color, alpha=1.0, soft=0.0, evenodd=False, light=False):
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
            M = blur(M, sg)
        M = (M * alpha)[..., None]
        col = np.asarray(color, np.float32)
        if light:
            L = self._light(bb)
            if L is not None:
                col = col * L
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - M)
        reg += col * M

    def pstroke(self, pts, w, color, alpha=0.9, key="", jitter=0.8):
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

    def shadow(self, polys, strength=0.45, soft=6.0, color=(0.25, 0.2, 0.3)):
        """soft multiplicative cast shadow"""
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys]
        sg = soft * self.z
        bb = self._bbox(sp, int(sg * 3 + 3))
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        M = blur(self._mask(sp, bb), sg) * strength
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - M[..., None] * (1 - np.asarray(color, np.float32)))

    # ---- glow
    def light(self, c, r, color, strength=0.5):
        sx, sy = self.S1(*c)
        rr = r * self.z
        x0, y0 = max(0, int(sx - 2.6 * rr)), max(0, int(sy - 2.6 * rr))
        x1, y1 = min(self.W, int(sx + 2.6 * rr)), min(self.H, int(sy + 2.6 * rr))
        if x1 - x0 < 2 or y1 - y0 < 2:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        g = strength * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * rr * rr))
        reg = self.img[y0:y1, x0:x1]
        gc = g[..., None] * np.asarray(color, np.float32)
        reg[:] = 1 - (1 - reg) * (1 - gc)

    def glow_poly(self, polys, color, strength=0.4, soft=20):
        if isinstance(polys, np.ndarray):
            polys = [polys]
        sp = [self.S(p) for p in polys]
        sg = soft * self.z
        bb = self._bbox(sp, int(sg * 2.5 + 3))
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        g = blur(self._mask(sp, bb), sg) * strength
        reg = self.img[y0:y1, x0:x1]
        gc = g[..., None] * np.asarray(color, np.float32)
        reg[:] = 1 - (1 - reg) * (1 - gc)

    # ---- text
    def text(self, s, x, y, size, color, bold=False, family="Inter", align="left", alpha=1.0,
             rot=0.0, jitter=0.6):
        rng = np.random.default_rng(hseed("txt", s, self.boil))
        sx, sy = self.S1(x, y)
        sx += rng.normal(0, jitter)
        sy += rng.normal(0, jitter)
        fs = size * self.z
        surf = cairo.ImageSurface(cairo.FORMAT_A8, self.W, self.H)
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
        M = np.ndarray(shape=(self.H, surf.get_stride()), dtype=np.uint8, buffer=surf.get_data())[:, :self.W]
        ys, xs = np.nonzero(M)
        if len(ys) == 0:
            return
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        m = (M[y0:y1, x0:x1].astype(np.float32) / 255 * alpha)[..., None]
        reg = self.img[y0:y1, x0:x1]
        reg *= (1 - m)
        reg += np.asarray(color, np.float32) * m


_VIG = {}


def grade(img, grain, vignette=0.3, flicker=0.0, bloom=0.35, saturation=1.3):
    """final look: bloom, colour grade (cool shadows, warm highlights), vignette, paper grain."""
    h, w, _ = img.shape
    if (h, w) not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = ((xx - w / 2) / (w * 0.6)) ** 2 + ((yy - h * 0.5) / (h * 0.58)) ** 2
        _VIG[(h, w)] = (1 - vignette * np.clip(d, 0, 1.8) ** 1.25).astype(np.float32)
    out = img.copy()
    if bloom > 0:
        lum = out.mean(2)
        hi = np.clip((lum - 0.62) / 0.38, 0, 1)[..., None] * out
        small = hi[::6, ::6]
        small = gaussian_filter(small, (7, 7, 0))
        big = zoom(small, (6, 6, 1), order=1)[:h, :w]
        out = 1 - (1 - out) * (1 - bloom * big)
    lum = out.mean(2, keepdims=True)
    out = np.clip(lum + (out - lum) * saturation, 0, 1)
    shadow_w = np.clip(1 - lum * 1.6, 0, 1)
    out = out + shadow_w * np.array([-0.012, 0.0, 0.035], np.float32)
    out *= _VIG[(h, w)][..., None] * (1 + flicker)
    out *= (1 + 0.025 * grain[..., None])
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
