# Date Night: AylluOS (15 s Reel)

An isometric, hand-drawn ink + gouache animation made entirely in code (pen hatching, painted textures, lamp-lit scene, drawings on twos).

- Output: `output/date_night_aylluos_1080x1920.mp4` (1080x1920, 9:16, H.264, 24 fps, 15 s)
- 180 unique drawings, each held for 2 frames ("on twos": 12 drawings/s at 24 fps)
- Isometric cut-away trattoria painted once at 2.6x (`iso_bg.py`); characters, table and props redrawn every drawing (`iso_scene.py`)
- Sketchy broken pen strokes, cross-hatching, gouache fills with brush texture, scene lighting shared by room and characters (`wc.py`)

## Re-render
```
pip install pycairo scipy numpy pillow     # plus ffmpeg on PATH
cd animation
python3 render.py video ../output/date_night_aylluos_1080x1920.mp4
python3 render.py sheet 5                  # contact sheet for checking
python3 render.py preview 0 90 150         # single drawings as PNG
```

## Shots
| time | shot |
|---|---|
| 0.0–4.25 s | Isometric wide, pushing in: couple laughing; phone on the table buzzes at 3.3 s, both freeze |
| 4.25–5.75 s | Medium: they look at each other, worried |
| 5.75–7.17 s | Wide: he picks up the phone |
| 7.17–10.67 s | Close-up: AylluOS notification "Baby is Sleeping / 8:31pm · Grandma" |
| 10.67–12.0 s | Medium: relief, smiles; phone goes face down |
| 12.0–15.0 s | They clink glasses, then the camera pulls back out to the whole diorama |
