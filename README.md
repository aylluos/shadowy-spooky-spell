# Date Night: AylluOS (15 s Reel)

A hand-drawn, watercolor-style animation made entirely in code.

- Output: `output/date_night_aylluos_1080x1920.mp4` (1080x1920, 9:16, H.264, 24 fps, 15 s)
- 180 unique drawings, each held for 2 frames ("on twos": 12 drawings/s at 24 fps)
- Line boil, watercolor washes (organic edges, pigment pooling, paper granulation) via cairo + numpy

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
| 0.0–4.25 s | Wide: couple laughing; phone on the table buzzes at 3.3 s, both freeze |
| 4.25–5.75 s | Medium: they look at each other, worried |
| 5.75–7.17 s | Wide: he picks up the phone |
| 7.17–10.67 s | Close-up: AylluOS notification "Baby is Sleeping / 8:31pm · Grandma" |
| 10.67–12.0 s | Medium: relief, smiles; phone goes face down |
| 12.0–15.0 s | Wide: they clink glasses and keep enjoying the evening |
