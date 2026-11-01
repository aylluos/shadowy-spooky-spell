// THE SONG: every sound comes from an event in score.js.   node song.js   (STEMS=1 writes stems)
const path = require('path');
const { SR, Bus, reverb, pingpong, rng } = require('./engine/audio/dsp');
const I = require('./engine/audio/instruments');
const MIX = require('./engine/audio/mix');
const { mtof } = require('./engine/music');
const sc = require('./score');
const { T, BEAT, DURATION, m, ev, clock } = sc;

const N = Math.ceil(DURATION * SR);
const bus = () => new Bus(N);
const drums = bus(), bass = bus(), pad = bus(), keys = bus(), lead = bus(), fx = bus(), amb = bus();
const verb = bus(), dly = bus();
const groove = (t) => t < ev.stop - BEAT / 2 || t >= ev.clink; // the band plays only while all is well (an 8th of held breath before the buzz)

// ---------- restaurant room tone: soft murmur bed, a cutlery clink now and then ----------
{
  const w = rng(7), out = new Float32Array(N);
  let a = 0, b = 0;
  for (let i = 0; i < N; i++) { a += 0.02 * (w() - a); b += 0.002 * (w() - b); out[i] = a * 0.6 + b * 2.2; }
  amb.addMono(out, 0, 0.05);
  for (const t of [0.9, 2.2, 13.1, 14.2]) amb.addMono(I.bell(3100 + t * 90, 0.08, 1.4, 2.76), t, 0.03, 0.4);
}

// ---------- the groove (lofi: swung kick/rim/hat, upright-ish bass, e-piano stabs) ----------
const K = I.kick({ tail: 0.2, punch: 0.45 }), R = I.rim(0.8, 3), Hh = [I.hat(false, 5), I.hat(false, 6)];
const kicks = [];
const swing = (s) => (s % 2 ? BEAT / 4 * 0.16 : 0);
clock.eachStep(0, 6, 16, (t0, b, s) => {
  const t = t0 + swing(s);
  if (!groove(t0)) return;
  if (s === 0 || s === 7 || s === 10) { drums.addMono(K, t, s === 0 ? 0.8 : 0.55); kicks.push(t); }
  if (s === 4 || s === 12) drums.addMono(R, t, 0.32, 0.15);
  if (s % 2 === 0) drums.addMono(Hh[(s / 2) % 2], t, s % 4 === 0 ? 0.1 : 0.06, -0.25);
});
clock.eachStep(0, 6, 8, (t, b, s) => {
  if (!groove(t)) return;
  const c = sc.chordAt(t); if (!c) return;
  const r = c.bass + 12;
  if (s === 0 || s === 3 || s === 5) bass.addMono(I.bass(s === 5 ? r + 7 : r, BEAT * (s === 0 ? 1.4 : 0.8), { bright: 0.25, sub: 0.9 }), t, 0.5);
  if (s === 0 || s === 3 || s === 6) for (const n of c.notes) keys.addMono(I.epiano(n, BEAT * 1.1, { index: 0.8 }), t + swing(1) * (s % 2), 0.06, 0.1);
});
for (const n of sc.hook) { const e = I.epiano(n.midi, n.dur * 1.4, { index: 1.1 }); lead.addMono(e, n.t, 0.3, 0.2); verb.addMono(e, n.t, 0.12); dly.addMono(e, n.t, 0.06); }

// ---------- the buzz: a phone vibrating on a wooden table (hard cut of the groove on the first) ----------
function buzz(len = 0.42) {
  const out = new Float32Array(Math.ceil(len * SR)), w = rng(11);
  for (let i = 0; i < out.length; i++) {
    const t = i / SR, env = Math.min(1, t / 0.01) * Math.min(1, (len - t) / 0.03);
    const motor = Math.sign(Math.sin(2 * Math.PI * 152 * t)) * 0.6 + Math.sin(2 * Math.PI * 304 * t) * 0.3;
    const rattle = w() * (0.5 + 0.5 * Math.sign(Math.sin(2 * Math.PI * 38 * t)));
    out[i] = (motor * 0.55 + rattle * 0.35) * env;
  }
  return out;
}
for (const [i, t] of ev.buzz.entries()) { fx.addMono(buzz(), t, i === 0 ? 0.42 : 0.36, 0.1); fx.addMono(I.thud(120, 0.03), t, 0.25); }
// the record stops: a tiny vinyl brake on the first buzz
fx.addMono(I.noiseSweep(0.18, 2200, 300, { q: 1.2, pink: true }), ev.stop + 0.02, 0.06);

// ---------- tension: a dark low pad and a heartbeat until the notification ----------
for (const c of sc.chords.filter((c) => c.t0 >= ev.worried && c.t0 < ev.relief)) {
  for (const n of c.notes) { const p = I.padNote(n - 12, c.t1 - c.t0 + 0.8, { cutoff: 700, attack: 0.6, release: 1.2 }); pad.addStereo(p.L, p.R, c.t0, 0.07); }
}
for (let k = 0; k < 6; k++) { const t = ev.worried + k * BEAT * 0.75; if (t < ev.notif - 0.1) fx.addMono(I.heartbeat(), t, 0.5); }

// ---------- the notification: a chime, then a music-box lullaby while he reads ----------
fx.addMono(I.ting(m('E6')), ev.notif, 0.45, 0.05);
verb.addMono(I.ting(m('E6')), ev.notif, 0.2);
for (const n of sc.lullaby) { const mb = I.musicBox(n.midi, { decay: 1.6 }); keys.addMono(mb, n.t, 0.22, -0.1); verb.addMono(mb, n.t, 0.2); dly.addMono(mb, n.t, 0.05); }

// ---------- relief: a warm open chord (a felt-piano hit), soft and rising ----------
for (const c of sc.chords.filter((c) => c.t0 >= ev.relief && c.t0 < ev.clink)) {
  for (const n of c.notes) {
    const p = I.padNote(n, c.t1 - c.t0 + 0.4, { cutoff: 1800, attack: 0.25, release: 0.9 }); pad.addStereo(p.L, p.R, c.t0, 0.07);
    keys.addMono(I.epiano(n, 1.4, { index: 0.6 }), c.t0, 0.11, 0);
  }
}
keys.addMono(I.epiano(m('F2'), 1.6, { index: 0.5 }), ev.relief, 0.22);
fx.addMono(I.thud(95, 0.06), ev.relief, 0.5); fx.addMono(I.bell(1760, 0.5, 0.8, 2.0), ev.relief, 0.12); // a soft felt hit marks the relief
fx.addMono(I.noiseSweep(BEAT * 0.9, 300, 5000, { q: 0.8, shape: (x) => x * x, pink: true }), ev.clink - BEAT, 0.12); // the glasses rise

// ---------- the clink: two wine glasses (two detuned glass partials), then the groove again ----------
for (const [f, g, p] of [[2637, 0.4, -0.15], [2793, 0.32, 0.15], [5274, 0.12, 0]]) {
  const b = I.bell(f, 0.55, 0.6, 2.76); fx.addMono(b, ev.clink, g, p); verb.addMono(b, ev.clink, g * 0.5);
}
for (const n of sc.chords.find((c) => c.t0 >= ev.clink).notes) { const p = I.padNote(n + 12, 2.6, { cutoff: 2600, attack: 0.05, release: 1.4 }); pad.addStereo(p.L, p.R, ev.clink, 0.05); }
for (const [i, h] of sc.hearts.entries()) { const mb = I.musicBox(m(['A6', 'C7', 'F7'][i])); keys.addMono(mb, h.t, 0.08, 0.3 - i * 0.3); }

// ---------- mix ----------
MIX.sidechain([pad, bass], kicks.filter((t) => t >= ev.clink));
const stems = {
  drums, bass, pad, keys, lead, fx, amb,
  verb: reverb(verb, { room: 0.84, damp: 0.4 }),
  dly: pingpong(dly, BEAT * 0.75, 0.3, 3500),
};
const GAIN = { drums: 0.55, bass: 0.65, pad: 2.2, keys: 1.15, lead: 1.6, fx: 0.85, amb: 1.0, verb: 1, dly: 0.9 };
const out = path.join(__dirname, 'out');
const mix = MIX.mixdown(stems, GAIN, { stemDir: process.env.STEMS ? out : null });
MIX.lofi(mix, { wow: 0.6, flutter: 0.5, lowpass: 9000 });
MIX.highpass(mix, 24);
MIX.fadeOut(mix, DURATION - 1.2, DURATION);
const M = MIX.master(mix, parseFloat(process.env.DRIVE || '0.8'), undefined, { lufs: process.env.LUFS ? parseFloat(process.env.LUFS) : -13 });
MIX.writeWav(path.join(out, 'music.wav'), mix);
console.log(`wrote out/music.wav (${DURATION.toFixed(2)}s${M.lufs !== undefined ? `, ${M.lufs.toFixed(1)} LUFS at drive ${M.drive.toFixed(2)}` : ''})`);
