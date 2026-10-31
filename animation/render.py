"""Render the isometric date-night animation.

    python3 render.py preview 0 40 90 150     # PNG stills of selected drawings
    python3 render.py sheet [step]            # contact sheet
    python3 render.py video out.mp4           # 15 s MP4, 1080x1920, 24 fps (drawings on twos)
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

from wc import Canvas, Textures, W, H, grade
import iso_bg
import iso_scene as scene

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("WC_CACHE", os.path.join(HERE, ".cache"))
os.makedirs(CACHE, exist_ok=True)
PAD = 100                      # world-px margin painted around the frame
SB = 2.6                       # background painted at 2.6x so camera push-ins stay sharp

_tex = None
_bg = {}


def tex():
    global _tex
    if _tex is None:
        _tex = Textures(CACHE)
    return _tex


def big_background():
    if "room" not in _bg:
        path = os.path.join(CACHE, "room_bg_v2.png")
        if not os.path.exists(path):
            cv = Canvas(tex(), cam=(540, 960, SB), size=(int((W + 2 * PAD) * SB), int((H + 2 * PAD) * SB)))
            cv.lightfn = iso_bg.make_light()
            iso_bg.draw_background(cv)
            Image.fromarray((np.clip(cv.img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
        _bg["room"] = Image.open(path).convert("RGB")
        _bg["room"].load()
    return _bg["room"]


def room_view(cam):
    cx, cy, z = cam
    x0, y0 = (cx - W / 2 / z + PAD) * SB, (cy - H / 2 / z + PAD) * SB
    x1, y1 = (cx + W / 2 / z + PAD) * SB, (cy + H / 2 / z + PAD) * SB
    im = big_background().resize((W, H), Image.LANCZOS, box=(x0, y0, x1, y1))
    return np.asarray(im, np.float32) / 255.0


def closeup_bg():
    if "phone" not in _bg:
        cv = Canvas(tex(), cam=(540, 960, 1.0), boil=0)
        scene.draw_closeup_bg(cv)
        _bg["phone"] = cv.img.copy()
    return _bg["phone"]


def render(i):
    kind = scene.shot_for(i)
    t = i / scene.FPS_DRAW
    cam = scene.cam_for(i)
    if kind == "phone":
        cv = Canvas(tex(), cam=cam, boil=i, base=closeup_bg())
        cv.lightfn = scene.closeup_light
        scene.draw_closeup(cv, t, i)
    else:
        cv = Canvas(tex(), cam=cam, boil=i, base=room_view(cam))
        rng = np.random.default_rng(i)
        cv.lightfn = iso_bg.make_light(candle=1.0 + rng.uniform(-0.06, 0.06))
        scene.draw_restaurant(cv, t, i, cam)
    flick = np.random.default_rng(i).uniform(-0.008, 0.008)
    return grade(cv.img, cv.grain, vignette=0.18, flicker=flick)


def main():
    mode = sys.argv[1]
    out_dir = os.environ.get("OUT", HERE)
    big_background()
    if mode == "preview":
        for a in sys.argv[2:]:
            Image.fromarray(render(int(a))).save(os.path.join(out_dir, f"d{int(a):03d}.png"))
    elif mode == "sheet":
        step = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        idx = list(range(0, scene.N_DRAWINGS, step))
        with Pool(4) as pool:
            imgs = pool.map(render, idx)
        cols = 6
        tw, th = W // 4, H // 4
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "white")
        for n, im in enumerate(imgs):
            sheet.paste(Image.fromarray(im).resize((tw, th), Image.LANCZOS), ((n % cols) * tw, (n // cols) * th))
        sheet.save(os.path.join(out_dir, "sheet.png"))
    elif mode == "video":
        out = sys.argv[2]
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", "24", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
               "-profile:v", "high", "-level", "4.2", "-movflags", "+faststart", out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for n, im in enumerate(pool.imap(render, range(scene.N_DRAWINGS), chunksize=2)):
                b = im.tobytes()
                proc.stdin.write(b)   # each drawing held for two frames -> 12 drawings/s at 24 fps
                proc.stdin.write(b)
                if n % 12 == 0:
                    print(f"drawing {n}/{scene.N_DRAWINGS}", flush=True)
        proc.stdin.close()
        proc.wait()
        print("wrote", out)


if __name__ == "__main__":
    main()
