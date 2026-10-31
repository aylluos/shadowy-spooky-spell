"""Render the date-night animation.

    python3 render.py preview 0 40 90 150     # PNG stills of selected drawings
    python3 render.py sheet                   # contact sheet of every 6th drawing
    python3 render.py video out.mp4           # full 15 s MP4, 1080x1920, 24 fps (drawings on twos)
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

from wc import Canvas, Textures, W, H
import scene

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("WC_CACHE", os.path.join(HERE, ".cache"))
os.makedirs(CACHE, exist_ok=True)

_tex = None
_bg = {}


def tex():
    global _tex
    if _tex is None:
        _tex = Textures(CACHE)
    return _tex


def background(kind):
    if kind not in _bg:
        cv = Canvas(tex(), cam=scene.CAMS[kind], boil=0)
        if kind == "phone":
            scene.draw_closeup_bg(cv)
        else:
            scene.draw_restaurant_bg(cv)
        _bg[kind] = cv.img.copy()
    return _bg[kind]


def render(i):
    kind = scene.shot_for(i)
    t = i / scene.FPS_DRAW
    cv = Canvas(tex(), cam=scene.CAMS[kind], boil=i, base=background(kind))
    if kind == "phone":
        scene.draw_closeup(cv, t, i)
    else:
        scene.draw_restaurant(cv, t, i)
    flick = np.random.default_rng(i).uniform(-0.008, 0.008)
    return cv.finish(vignette=0.24, flicker=flick)


def main():
    mode = sys.argv[1]
    out_dir = os.environ.get("OUT", HERE)
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
