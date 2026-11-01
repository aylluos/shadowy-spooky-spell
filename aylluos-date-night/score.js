// AYLLUOS · DATE NIGHT (9:16 Reel, 15 s). The single source of truth for music AND picture.
// Story: a couple laughing on a date night -> the phone buzzes (the music stops) -> worried look ->
// he reads it: AylluOS "Baby is Sleeping · 8:31pm · Grandma" (a lullaby plays) -> relief -> they clink
// glasses on the downbeat and the groove comes back.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const { m, makeClock, placeBar, makeChords } = MU;

  const FPS = 24;                 // 24 fps film, drawings held on twos (12 drawings per second)
  const DRAW_FPS = 12;
  const FORMAT = '9:16';
  const STYLE = 'watercolor';
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const clock = makeClock({ bpm: 96, offset: 0 });   // 1 bar = 2.5 s
  const { T, BEAT, BAR } = clock;
  const DURATION = T(6);                             // 15.0 s

  const ev = {
    buzz: [T(1, 2), T(1, 3), T(2, 1)],   // three vibrations; the first one kills the groove
    stop: T(1, 2),
    worried: T(2, 0),                    // cut: two-shot, worried faces, heartbeat starts
    grab: T(2, 1),                       // he reaches for the phone
    phone: T(2, 2),                      // cut: phone close-up in his hands
    notif: T(2, 3),                      // the AylluOS notification pops (chime)
    relief: T(4, 0),                     // cut back to them: relief, warm chord
    raise: T(4, 3),                      // glasses come up (anticipation)
    clink: T(5, 0),                      // the clink, groove returns
    end: DURATION,
  };

  const S = {
    date: [0, ev.worried], worried: [ev.worried, ev.phone], phone: [ev.phone, ev.relief],
    relief: [ev.relief, ev.clink], cheers: [ev.clink, DURATION],
  };

  const { chords, chordAt } = makeChords(clock, {
    Fmaj7: { notes: ['A3', 'C4', 'E4', 'F4'], bass: 'F1' },
    Dm9: { notes: ['F3', 'A3', 'C4', 'E4'], bass: 'D2' },
    Bbmaj7: { notes: ['A3', 'D4', 'F4', 'Bb4'], bass: 'Bb1' },
    Gm9: { notes: ['F3', 'Bb3', 'D4', 'A4'], bass: 'G1' },
    C7sus: { notes: ['F3', 'Bb3', 'C4', 'E4'], bass: 'C2' },
    Dmadd9: { notes: ['D3', 'F3', 'A3', 'E4'], bass: 'D1' },
  }, [
    [0, 0, 4, 'Fmaj7'], [1, 0, 2, 'Dm9'], [1, 2, 2, 'Dm9'],
    [2, 0, 4, 'Dmadd9'], [3, 0, 4, 'Bbmaj7'],
    [4, 0, 2, 'Gm9'], [4, 2, 2, 'C7sus'], [5, 0, 4, 'Fmaj7'],
  ]);

  // the hook (8th grid): a happy little e-piano line, played at the start and again after the clink
  const HOOK = [['C5', 0, 1], ['F5', 1, 1], ['A5', 2, 2], ['G5', 4, 1], ['F5', 5, 1], ['E5', 6, 1], ['F5', 7, 1]];
  const HOOK2 = [['A5', 0, 1], ['C6', 1, 1], ['A5', 2, 1], ['G5', 3, 1], ['F5', 4, 2], ['C5', 6, 2]];
  const hook = [...placeBar(clock, HOOK, 0), ...placeBar(clock, HOOK2, 5)];
  // a lullaby on the music box while he reads "Baby is Sleeping" (bar 3)
  const LULL = [['F5', 0, 2], ['A5', 2, 1], ['C6', 3, 1], ['A5', 4, 2], ['G5', 6, 2]];
  const lullaby = [...placeBar(clock, LULL, 3)].filter((n) => n.t > ev.notif);
  lullaby.unshift({ t: ev.notif + BEAT * 0.5, dur: BEAT, midi: m('C6') });

  // laughter bounces on the beat during the date and after the clink
  const laughBeats = [];
  for (let b = 0; b < 6; b++) for (let k = 0; k < 4; k++) {
    const t = T(b, k);
    if (t < ev.stop - 0.01 || t >= ev.clink + BEAT) laughBeats.push(t);
  }
  // little hearts drift up after the clink, one per beat
  const hearts = [T(5, 1), T(5, 2), T(5, 3)].map((t, i) => ({ t, x: [-40, 30, -10][i], seed: i }));
  const blinks = [1.3, 2.9, 5.4, 11.2, 13.6];

  const markers = {
    buzz: { t: ev.buzz[0], sync: 'a' },
    worried: { t: ev.worried, sync: 'av' },
    phone: { t: ev.phone, sync: 'v' },
    notif: { t: ev.notif, sync: 'av' },
    relief: { t: ev.relief, sync: 'av' },
    raise: ev.raise,
    clink: { t: ev.clink, sync: 'av' },
    hearts: T(5, 2),
  };

  const SCORE = {
    FPS, DRAW_FPS, FORMAT, STYLE, W, H, SAFE, DURATION, clock, T, BEAT, BAR, S, m, chords, chordAt,
    ev, hook, lullaby, laughBeats, hearts, blinks, markers,
  };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
