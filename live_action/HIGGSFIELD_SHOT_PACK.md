# Date Night: live-action version (Higgsfield shot pack)

Same story as the animation, as a photoreal 15 s vertical Reel (9:16, 1080x1920).

**Plan:** make two character reference stills first. Then generate each shot as **image-to-video**, using a start frame made with those references so the couple looks the same in every shot. Cut the clips together and add the phone screen as an image (AI video can't render exact notification text).

---

## 1. Characters (generate these stills first)

Use the same wording every time you mention them.

**Her:** woman in her early 30s, warm olive skin, long wavy chestnut-brown hair worn loose over one shoulder, soft natural makeup, small gold hoop earrings, thin gold necklace, sleeveless lavender satin slip dress.

**Him:** man in his early 30s, light-medium skin, short tousled dark-brown hair, light stubble, deep indigo blazer over an open-collar white shirt.

Reference still prompt (one per person, then one of both together):
> Photoreal portrait, [character description], seated at a small round candlelit restaurant table, warm tungsten light from a low pendant lamp, shallow depth of field, cozy Italian trattoria at night with string lights and wine bottles softly out of focus behind, 35mm film look, natural skin texture, vertical 9:16.

**Setting:** a small candlelit trattoria at night. Round table with a cream tablecloth, a single candle, a small vase with one red rose, two glasses of red wine. Warm amber light, string lights, a window with city lights behind. The colours match the brand: lavender and indigo outfits against warm amber.

---

## 2. Shots

Total 15 s. Durations are targets; trim in the edit.

### Shot 1: laughing (0.0–3.5 s)
- **Start frame:** both at the table, mid-laugh, glasses in hand; her phone-side hand near his phone lying face-up on the table.
- **Video prompt:**
  > Photoreal, a couple on a date night laughing together at a candlelit restaurant table, she laughs with her head tilted back, he grins and gestures with his wine glass, candle flicker, warm light, slow push-in, handheld cinematic feel, 9:16.
- **Camera:** slow push-in, eye level, two-shot.

### Shot 2: the buzz (3.5–5.0 s)
- **Video prompt:**
  > Close on the restaurant table: a smartphone lying on the white tablecloth lights up and vibrates; at the edges of frame the couple's laughter stops and their hands freeze; shallow depth of field, warm candlelight.
- **Camera:** static macro on the phone; or a quick tilt down from their faces to the phone.

### Shot 3: worried look (5.0–6.5 s)
- **Video prompt:**
  > Medium two-shot, the couple stop laughing and look at each other with worried expressions, eyebrows raised, a tense quiet moment, candlelight on their faces.
- **Camera:** slow push-in on the faces.

### Shot 4: he picks up the phone (6.5–7.5 s)
- **Video prompt:**
  > The man reaches for the phone on the table and lifts it toward himself, the woman leans in anxiously with her hand on her chest, warm restaurant lighting.

### Shot 5: phone close-up (7.5–10.5 s), hold long enough to read
- **Video prompt (hands only):**
  > Over-the-shoulder close-up of a man's hands holding a smartphone upright in a candlelit restaurant, the screen glowing, thumbs resting on the sides, background softly blurred with warm bokeh, very little movement, 9:16.
- **Phone screen:** generate it with a **plain bright screen**, then put `lock_screen_1170x2532.png` onto the screen in the editor (corner-pin / screen replacement; CapCut, Premiere and After Effects can all do this). The notification text then stays sharp and correct.
- **Easier option:** use our existing animated close-up (`output/date_night_aylluos_1080x1920.mp4`, 7.17–10.67 s) as an illustrated insert. The cut from live action to illustration works as a deliberate brand moment.

### Shot 6: relief (10.5–12.0 s)
- **Video prompt:**
  > Medium two-shot, the couple look at each other and their worry melts into big relieved smiles, he exhales and laughs softly, she puts her hand on her heart, he sets the phone face down on the table.

### Shot 7: cheers (12.0–15.0 s)
- **Video prompt:**
  > The couple raise their glasses of red wine and clink them together over the candle, laughing, a warm romantic moment, then lean toward each other and keep enjoying the evening; slow pull-back revealing the cozy candlelit trattoria with string lights.
- **Camera:** clink in the centre of frame, then a slow pull-back.

---

## 3. Settings for every clip
- **Aspect:** 9:16 vertical. Keep faces and the clink in the centre band; Instagram's caption overlays the bottom ~20%.
- **Look:** warm tungsten / candlelight, shallow depth of field, natural skin, light film grain.
- **Negative prompt:** text, captions, logos, watermarks, extra fingers, distorted hands, extra people, phone screen text.
- **Consistency:** reuse the same reference stills (or Higgsfield's character feature, if your plan has it) and the same character wording in every prompt.

## 4. Edit
1. Lay the clips out on the 15 s timeline above.
2. Screen-replace shot 5 with `lock_screen_1170x2532.png`.
3. Sound: soft restaurant ambience, a phone buzz at 3.5 s, a glass clink at 12.5 s, and gentle music under it.
4. Export 1080x1920, H.264, 30 fps (or 24 fps for a filmic feel).

## 5. Before posting
These are AI-generated people. Turn on Instagram's **AI label** when you post (in Metricool: `instagramData.isAiGenerated: true`). Don't use a real person's face or name without their consent.

---

## Files
- `lock_screen_1170x2532.png`: the phone screen (AylluOS logo, "Baby is Sleeping", "8:31pm · Grandma", sleeping-baby art)
- `make_screen.py`: regenerates the screen (`python3 make_screen.py`)
