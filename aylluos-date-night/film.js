// THE FILM (9:16): an isometric cut-away trattoria in watercolour, a couple drawn in the AylluOS baby
// illustration style, and a crisp phone close-up. Every frame is a pure function of t. Character
// motion is sampled at 12 drawings per second (on twos at 24 fps); lines boil at the same rate.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, UI = globalThis.UI, S = globalThis.SCORE, Studio = globalThis.Studio;
  const { T, BEAT, ev } = S;
  const { clamp, lerp, ease } = U;
  const W = G.W, H = G.H, SAFE = G.SAFE;
  G.setStyle(G.styleName || 'watercolor', { boilFps: S.DRAW_FPS, lw: 0.65 });

  // ---------- brand ----------
  const B = { indigo: '#5A31F4', lav: '#A99FF0', seed: '#F47721', soft: '#EFEDFF', ink: '#172033' };
  UI.setTheme({ accent: B.indigo, accent2: B.lav, ink: B.ink, muted: '#5B6478', app: B.soft });
  const LINE = '#5A3A2E';                   // warm brown outlines, like the app illustrations
  const C = {
    wallA: '#E9B98F', wallB: '#D9A07C', wain: '#7A4A35', floor: '#B07A52', rug: '#7E3B52', slab: '#5C3A2A',
    night: '#1E2350', cloth: '#FBF4EA', candle: '#FFF3D6', wood: '#8A5638', bottle: ['#3F6B4A', '#7A2E3A', '#8A5A2A', '#2F5A55'],
    skinW: '#FBD3BD', skinM: '#F2C2A2', cheek: '#F79A9A', hairW: '#8A4E2B', hairM: '#5E3A22', hairHL: '#C4834F',
    dress: B.lav, dressDark: '#8E82E8', blazer: '#3B2A8F', shirt: '#FFFFFF', wine: '#7A1730',
  };
  let logoImg = null, babyImg = null;

  // drawings on twos: every pose is sampled at 12 per second
  const qt = (t) => Math.floor(t * S.DRAW_FPS + 1e-6) / S.DRAW_FPS;
  const K = (t, kf) => {               // keyframes for numbers AND [x, y] points
    if (!Array.isArray(kf[0][1])) return U.keys(t, kf);
    return [0, 1].map((i) => U.keys(t, kf.map((k) => [k[0], k[1][i], k[2]])));
  };

  // ---------- isometric projection ----------
  const OX = 540, OY = 900, L = 560, HW = 520;
  const P = (x, y, z = 0) => [OX + (x - y) * 0.866, OY + (x + y) * 0.5 - z];
  const PA = (arr) => arr.map((p) => P(p[0], p[1], p[2] || 0));
  const circ = (cx, cy, r, z, n = 40) => { const o = []; for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; o.push(P(cx + r * Math.cos(a), cy + r * Math.sin(a), z)); } return o; };

  // opaque under-painting + watercolour wash on top, so washes never show what is behind a character
  function paint(ctx, pts, fill, o = {}) {
    if (pts.length < 14) pts = G.polyPts(pts, 16);
    ctx.save(); ctx.beginPath(); G.path(ctx, pts, true); ctx.fillStyle = o.under || G.tint(fill, 0.12); ctx.fill(); ctx.restore();
    G.shape(ctx, pts, Object.assign({ fill, stroke: LINE, lw: 3.4, seed: 1 }, o));
  }
  const ell = (cx, cy, rx, ry, n) => G.ellPts(cx, cy, rx, ry, n);

  // ======================= THE ROOM (static painting) =======================
  function room(ctx, t) {
    // night outside the cut-away
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, '#141838'); sky.addColorStop(0.55, '#2B2560'); sky.addColorStop(1, '#3A2D6E');
    ctx.fillStyle = sky; ctx.fillRect(-W, -H, 3 * W, 3 * H);
    for (let i = 0; i < 70; i++) {
      const x = G.rnd(i, 1) * W, y = G.rnd(i, 2) * H, r = 1 + G.rnd(i, 3) * 2.2;
      ctx.globalAlpha = 0.25 + 0.5 * G.rnd(i, 4) * (0.7 + 0.3 * Math.sin(t * 2 + i)); ctx.fillStyle = '#FFF3D6';
      ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
    }
    ctx.globalAlpha = 1;
    // slab (diorama base)
    paint(ctx, PA([[0, L, 0], [L, L, 0], [L, L, -46], [0, L, -46]]), C.slab, { seed: 2, lw: 3 });
    paint(ctx, PA([[L, 0, 0], [L, L, 0], [L, L, -46], [L, 0, -46]]), G.tint(C.slab, -0.2), { seed: 3, lw: 3 });
    // floor + planks
    paint(ctx, PA([[0, 0, 0], [L, 0, 0], [L, L, 0], [0, L, 0]]), C.floor, { seed: 4 });
    for (let y = 40; y < L; y += 40) G.line(ctx, [P(0, y), P(L, y)], { color: 'rgba(80,45,25,0.35)', lw: 1.6, seed: 40 + y, step: 30 });
    // walls
    paint(ctx, PA([[0, 0, 0], [L, 0, 0], [L, 0, HW], [0, 0, HW]]), C.wallA, { seed: 5 });
    paint(ctx, PA([[0, 0, 0], [0, L, 0], [0, L, HW], [0, 0, HW]]), C.wallB, { seed: 6 });
    paint(ctx, PA([[0, 0, 0], [L, 0, 0], [L, 0, 110], [0, 0, 110]]), C.wain, { seed: 7 });
    paint(ctx, PA([[0, 0, 0], [0, L, 0], [0, L, 110], [0, 0, 110]]), G.tint(C.wain, -0.12), { seed: 8 });
    // wall tops (the cut) and end faces
    paint(ctx, PA([[-18, -18, HW], [L, -18, HW], [L, 0, HW], [0, 0, HW], [0, L, HW], [-18, L, HW]]), '#F4E6D2', { seed: 9, lw: 2.6 });
    paint(ctx, PA([[L, 0, -46], [L, -18, -46], [L, -18, HW], [L, 0, HW]]), '#C99A7A', { seed: 10, lw: 2.6 });
    paint(ctx, PA([[0, L, -46], [-18, L, -46], [-18, L, HW], [0, L, HW]]), '#E0B896', { seed: 11, lw: 2.6 });
    // the window on wall A: night city
    const win = PA([[250, 0, 210], [470, 0, 210], [470, 0, 420], [430, 0, 455], [360, 0, 470], [290, 0, 455], [250, 0, 420]]);
    paint(ctx, win, C.night, { seed: 12, under: '#1A1E46' });
    for (let i = 0; i < 26; i++) {
      const u = 262 + G.rnd(i, 9) * 196, z = 220 + G.rnd(i, 10) * 120;
      const p = P(u, 0, z); ctx.fillStyle = '#FFD27A'; ctx.globalAlpha = 0.85; ctx.fillRect(p[0], p[1], 5, 7); ctx.globalAlpha = 1;
    }
    { const m = P(300, 0, 430); ctx.fillStyle = '#FFF4D0'; ctx.beginPath(); ctx.arc(m[0], m[1], 13, 0, 7); ctx.fill(); }
    G.line(ctx, [P(360, 0, 210), P(360, 0, 468)], { color: '#F1E2C8', lw: 6, seed: 13 });
    G.line(ctx, [P(250, 0, 330), P(470, 0, 330)], { color: '#F1E2C8', lw: 6, seed: 14 });
    G.shape(ctx, G.polyPts(win, 16), { stroke: '#F1E2C8', lw: 9, seed: 15 });
    // shutters + flower box
    paint(ctx, PA([[200, 0, 210], [240, 0, 210], [240, 0, 440], [200, 0, 440]]), '#4E7A68', { seed: 16 });
    paint(ctx, PA([[480, 0, 210], [520, 0, 210], [520, 0, 440], [480, 0, 440]]), '#4E7A68', { seed: 17 });
    paint(ctx, PA([[240, 0, 185], [480, 0, 185], [480, 0, 208], [240, 0, 208]]), '#9A5A3A', { seed: 18 });
    for (let i = 0; i < 9; i++) { const p = P(255 + i * 26, 0, 214 + (i % 2) * 6); G.ellipse(ctx, p[0], p[1], 8, 7, { fill: i % 3 ? '#E86A7A' : B.lav, lw: 2, seed: 60 + i }); }
    // shelves with wine bottles on wall B
    for (const zs of [270, 350]) {
      paint(ctx, PA([[0, 90, zs], [26, 90, zs], [26, 330, zs], [0, 330, zs]]), '#7A4A30', { seed: 19 + zs, lw: 2.4 });
      for (let i = 0; i < 7; i++) {
        const b = P(12, 110 + i * 32, zs), h = 44 + (i % 3) * 8;
        const pts = [[b[0] - 7, b[1]], [b[0] + 7, b[1]], [b[0] + 7, b[1] - h * 0.6], [b[0] + 3, b[1] - h * 0.78], [b[0] + 3, b[1] - h], [b[0] - 3, b[1] - h], [b[0] - 3, b[1] - h * 0.78], [b[0] - 7, b[1] - h * 0.6]];
        paint(ctx, G.polyPts(pts, 8), C.bottle[i % 4], { seed: 30 + i + zs, lw: 2 });
      }
    }
    // framed picture on wall B
    paint(ctx, PA([[0, 380, 260], [0, 500, 260], [0, 500, 380], [0, 380, 380]]), '#6B4A2E', { seed: 20 });
    paint(ctx, PA([[0, 392, 272], [0, 488, 272], [0, 488, 368], [0, 392, 368]]), '#CFE0E6', { seed: 21 });
    paint(ctx, PA([[0, 392, 272], [0, 430, 320], [0, 455, 300], [0, 488, 335], [0, 488, 272]]), '#7FA86E', { seed: 22 });
    // plant in the right corner
    paint(ctx, PA([[480, 40, 0], [540, 40, 0], [540, 40, 70], [480, 40, 70]]), '#B8643C', { seed: 23 });
    { const b = P(510, 40, 70); for (let i = 0; i < 9; i++) { const a = -2.7 + i * 0.27, r = 46 + 20 * G.rnd(i, 30); G.ellipse(ctx, b[0] + Math.cos(a) * r, b[1] + Math.sin(a) * r, 22, 9, { fill: '#4F8A5B', lw: 2, seed: 70 + i }); } }
    // rug
    paint(ctx, circ(280, 280, 210, 0.5), C.rug, { seed: 24 });
    G.shape(ctx, circ(280, 280, 180, 0.5), { stroke: '#E8B86A', lw: 2.4, seed: 25 });
    // string lights along both wall tops
    for (const wall of [0, 1]) {
      const pts = [];
      for (let i = 0; i <= 24; i++) { const u = 10 + (i / 24) * (L - 20), sag = 18 * Math.abs(Math.sin((i / 24) * Math.PI * 4)); pts.push(wall ? P(4, u, HW - 18 - sag) : P(u, 4, HW - 18 - sag)); }
      G.line(ctx, pts, { color: '#3A2A24', lw: 1.6, seed: 80 + wall, step: 12 });
      for (let i = 1; i < 24; i += 2) { const p = pts[i]; glow(ctx, p[0], p[1] + 6, 22, 'rgba(255,214,140,0.55)'); ctx.fillStyle = '#FFE8A8'; ctx.beginPath(); ctx.ellipse(p[0], p[1] + 6, 4, 5.5, 0, 0, 7); ctx.fill(); }
    }
    // pendant lamp over the table (cord to the top of frame)
    const lp = P(280, 280, 330);
    G.line(ctx, [[lp[0], -400], [lp[0], lp[1] - 30]], { color: '#2A201C', lw: 2, seed: 90, amp: 0.4 });
    paint(ctx, G.polyPts([[lp[0] - 46, lp[1]], [lp[0] - 34, lp[1] - 22], [lp[0] - 10, lp[1] - 32], [lp[0] + 10, lp[1] - 32], [lp[0] + 34, lp[1] - 22], [lp[0] + 46, lp[1]]], 10), '#3E5A50', { seed: 91 });
    ctx.fillStyle = '#FFF0C2'; ctx.beginPath(); ctx.ellipse(lp[0], lp[1], 42, 7, 0, 0, 7); ctx.fill();
  }
  function glow(ctx, x, y, r, col) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, col); g.addColorStop(1, 'rgba(255,200,120,0)');
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore();
  }

  function chair(ctx, x, y, f, seed) {
    // a bistro chair seen from 3/4: back behind the sitter, seat at hip height
    paint(ctx, G.polyPts([[x - f * 58, y - 128], [x - f * 44, y - 128], [x - f * 40, y + 6], [x - f * 54, y + 6]], 14), C.wood, { seed, lw: 2.6 });
    paint(ctx, G.polyPts([[x - 46, y - 4], [x + 46, y - 4], [x + 40, y + 12], [x - 40, y + 12]], 14), G.tint(C.wood, 0.1), { seed: seed + 1, lw: 2.6 });
    for (const dx of [-38, 36]) G.line(ctx, [[x + dx, y + 12], [x + dx * 1.05, y + 78]], { color: '#4A2E20', lw: 4, seed: seed + dx });
  }

  // ======================= THE COUPLE (AylluOS baby style) =======================
  const HEAD_R = 44;
  function eyesDraw(ctx, ex, ey, o, female, side) {
    const { eyes, look = [0, 0], worry = 0 } = o;
    const rx = 9.2, ry = eyes === 'wide' ? 12.6 : 11;
    ctx.save();
    ctx.lineCap = 'round'; ctx.strokeStyle = '#2A1A14';
    if (eyes === 'happy') { ctx.lineWidth = 2.8; ctx.beginPath(); ctx.moveTo(ex - rx, ey + 2); ctx.quadraticCurveTo(ex, ey - 9, ex + rx, ey + 2); ctx.stroke(); ctx.restore(); return; }
    if (eyes === 'closed') {
      ctx.lineWidth = 2.6; ctx.beginPath(); ctx.moveTo(ex - rx, ey); ctx.quadraticCurveTo(ex, ey + 6, ex + rx, ey); ctx.stroke();
      if (female) { ctx.lineWidth = 1.6; for (const k of [0.5, 0.9]) { ctx.beginPath(); ctx.moveTo(ex + side * rx * k, ey + 3); ctx.lineTo(ex + side * (rx * k + 3), ey + 7); ctx.stroke(); } }
      ctx.restore(); return;
    }
    // white, iris with a glossy gradient, pupil, two highlights (like the app's baby)
    ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.ellipse(ex, ey, rx, ry, 0, 0, 7); ctx.fill();
    ctx.save(); ctx.beginPath(); ctx.ellipse(ex, ey, rx, ry, 0, 0, 7); ctx.clip();
    const ix = ex + look[0] * 2.6, iy = ey + look[1] * 2.8 + 1, ir = eyes === 'wide' ? 6.8 : 7.6;
    const g = ctx.createLinearGradient(ix, iy - ir, ix, iy + ir);
    g.addColorStop(0, '#3A1E10'); g.addColorStop(1, '#9A5A2C');
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(ix, iy, ir, ir * 1.08, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#120806'; ctx.beginPath(); ctx.ellipse(ix, iy + 0.5, ir * 0.48, ir * 0.52, 0, 0, 7); ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(ix - 2.8, iy - 3.4, 2.7, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.arc(ix + 2.6, iy + 3.2, 1.2, 0, 7); ctx.fill();
    // lid + lashes
    ctx.lineWidth = 2.6; ctx.beginPath(); ctx.ellipse(ex, ey, rx + 0.6, ry + 0.6, 0, Math.PI * 1.04, Math.PI * 1.96); ctx.stroke();
    ctx.lineWidth = 1.5;
    for (let k = 0; k < (female ? 3 : 1); k++) { const yy = ey - ry * (0.2 + 0.32 * k); ctx.beginPath(); ctx.moveTo(ex + side * (rx - 1), yy); ctx.lineTo(ex + side * (rx + 4 - k), yy - 3 - k); ctx.stroke(); }
    ctx.restore();
  }

  function person(ctx, o) {
    const { x, y, f, female, bob = 0, tilt = 0 } = o;
    const skin = female ? C.skinW : C.skinM, hair = female ? C.hairW : C.hairM;
    const sd = female ? 100 : 200;
    ctx.save(); ctx.translate(x, y - bob);
    // long hair behind (her)
    const hc = [f * 6, -168];
    if (female) {
      ctx.save(); ctx.translate(hc[0], hc[1]); ctx.rotate(tilt);
      paint(ctx, G.polyPts([[-f * 50, -30], [-f * 40, -54], [0, -60], [f * 42, -40], [f * 50, 20], [f * 40, 80], [-f * 6, 96], [-f * 52, 92], [-f * 60, 30]], 14), hair, { seed: sd });
      ctx.restore();
    }
    // torso
    if (female) {
      paint(ctx, G.polyPts([[-36, -122], [36, -122], [40, -70], [34, 0], [-34, 0], [-40, -70]], 14), skin, { seed: sd + 1 });
      paint(ctx, G.polyPts([[-38, -96], [-18, -88], [0, -94], [18, -88], [38, -96], [42, -60], [36, 4], [-36, 4], [-42, -60]], 12), C.dress, { seed: sd + 2 });
      G.line(ctx, [[-24, -122], [-26, -94]], { color: C.dressDark, lw: 3, seed: sd + 3 });
      G.line(ctx, [[24, -122], [26, -94]], { color: C.dressDark, lw: 3, seed: sd + 4 });
      ctx.fillStyle = '#E8B04A'; ctx.beginPath(); ctx.arc(f * 2, -104, 3, 0, 7); ctx.fill();
    } else {
      paint(ctx, G.polyPts([[-16, -128], [16, -128], [16, -112], [-16, -112]], 10), skin, { seed: sd + 1, lw: 2 });
      paint(ctx, G.polyPts([[-40, -118], [40, -118], [44, -60], [38, 4], [-38, 4], [-44, -60]], 14), C.blazer, { seed: sd + 2 });
      paint(ctx, G.polyPts([[-16, -118], [16, -118], [0, -70]], 8), C.shirt, { seed: sd + 3, lw: 2.4 });
      paint(ctx, G.polyPts([[-14, -124], [0, -110], [-20, -106]], 6), C.shirt, { seed: sd + 4, lw: 2 });
      paint(ctx, G.polyPts([[14, -124], [0, -110], [20, -106]], 6), C.shirt, { seed: sd + 5, lw: 2 });
      G.line(ctx, [[-16, -116], [-26, -84], [0, -60]], { color: '#24195E', lw: 2.4, seed: sd + 6 });
      G.line(ctx, [[16, -116], [26, -84], [0, -60]], { color: '#24195E', lw: 2.4, seed: sd + 7 });
      ctx.fillStyle = B.seed; ctx.beginPath(); ctx.moveTo(-f * 30, -92); ctx.lineTo(-f * 22, -92); ctx.lineTo(-f * 26, -84); ctx.fill(); // pocket square (Seed accent)
    }
    // head
    ctx.save(); ctx.translate(hc[0], hc[1]); ctx.rotate(tilt);
    const ear = [-f * 40, 6];
    paint(ctx, ell(ear[0], ear[1], 9, 12), skin, { seed: sd + 10, lw: 2.4 });
    ctx.fillStyle = 'rgba(230,120,120,0.35)'; ctx.beginPath(); ctx.ellipse(ear[0], ear[1], 4, 7, 0, 0, 7); ctx.fill();
    const head = G.polyPts([[0, -46], [30, -40], [44, -14], [44, 14], [34, 36], [12, 46], [-12, 46], [-34, 36], [-44, 14], [-44, -14], [-30, -40]], 9);
    // soft round head: radial skin gradient (lit from the front), watercolour edge on top
    ctx.save(); ctx.beginPath(); G.path(ctx, head, true);
    const sg = ctx.createRadialGradient(f * 12, -12, 6, 0, 4, 58);
    sg.addColorStop(0, G.tint(skin, 0.35)); sg.addColorStop(0.7, skin); sg.addColorStop(1, G.tint(skin, -0.12));
    ctx.fillStyle = sg; ctx.fill(); ctx.restore();
    G.shape(ctx, head, { stroke: LINE, lw: 3, seed: sd + 11 });
    const fx = f * 10;
    // rosy cheeks
    for (const cx of [fx - 22, fx + 24]) { const cg = ctx.createRadialGradient(cx, 14, 0, cx, 14, 14); cg.addColorStop(0, `rgba(247,130,130,${0.45 + 0.3 * (o.blush || 0)})`); cg.addColorStop(1, 'rgba(247,130,130,0)'); ctx.fillStyle = cg; ctx.fillRect(cx - 16, -2, 32, 32); }
    eyesDraw(ctx, fx - 16, 2, o, female, -1);
    eyesDraw(ctx, fx + 17, 2, o, female, 1);
    // brows (worry lifts the inner ends)
    ctx.strokeStyle = G.tint(hair, -0.2); ctx.lineWidth = female ? 2.2 : 3; ctx.lineCap = 'round';
    for (const [bx, sgn] of [[fx - 16, -1], [fx + 17, 1]]) {
      const by = -14 - (o.raise || 0) * 4, w = o.worry || 0;
      ctx.beginPath(); ctx.moveTo(bx + sgn * 9, by + 2 + w * 2); ctx.quadraticCurveTo(bx, by - 3, bx - sgn * 8, by + 1 - w * 6); ctx.stroke();
    }
    // button nose
    ctx.fillStyle = 'rgba(214,120,96,0.35)'; ctx.beginPath(); ctx.ellipse(fx + f * 2, 16, 4.5, 3.4, 0, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.beginPath(); ctx.arc(fx + f * 1, 14.5, 1.3, 0, 7); ctx.fill();
    // mouth
    const mx = fx + f * 1, my = 27, mo = o.mouth || 'smile';
    ctx.strokeStyle = '#9A3A36'; ctx.lineWidth = 2.2;
    if (mo === 'laugh' || mo === 'open' || mo === 'o') {
      const w = mo === 'o' ? 4.5 : 8, h = mo === 'o' ? 6 : 5 + 4 * (o.open || 0.6);
      ctx.fillStyle = '#7A1E2A'; ctx.beginPath();
      if (mo === 'o') ctx.ellipse(mx, my + 2, w, h, 0, 0, 7); else { ctx.moveTo(mx - w, my); ctx.quadraticCurveTo(mx, my - 2, mx + w, my); ctx.quadraticCurveTo(mx, my + h * 2, mx - w, my); }
      ctx.fill();
      ctx.save(); ctx.clip(); ctx.fillStyle = '#F07A82'; ctx.beginPath(); ctx.ellipse(mx, my + h * 1.4, w * 0.6, h * 0.6, 0, 0, 7); ctx.fill(); ctx.restore();
    } else if (mo === 'wavy') {
      ctx.beginPath(); ctx.moveTo(mx - 7, my + 2); ctx.quadraticCurveTo(mx - 3.5, my - 2, mx, my + 1); ctx.quadraticCurveTo(mx + 3.5, my + 4, mx + 7, my); ctx.stroke();
    } else { // smile
      ctx.beginPath(); ctx.moveTo(mx - 7, my - 1); ctx.quadraticCurveTo(mx, my + 5, mx + 7, my - 1); ctx.stroke();
    }
    // tousled hair cap with a fringe and a highlight
    const fr = female
      ? [[-f * 46, 6], [-f * 48, -26], [-f * 30, -48], [0, -56], [f * 30, -50], [f * 48, -26], [f * 48, 2], [f * 38, -16], [f * 26, -24], [f * 16, -18], [f * 4, -28], [-f * 10, -20], [-f * 24, -26], [-f * 36, -12]]
      : [[-f * 46, 4], [-f * 48, -26], [-f * 32, -48], [-f * 4, -58], [f * 26, -54], [f * 46, -32], [f * 48, -12], [f * 36, -20], [f * 30, -12], [f * 20, -24], [f * 10, -16], [-f * 2, -26], [-f * 14, -18], [-f * 26, -26], [-f * 38, -12]];
    paint(ctx, G.polyPts(fr, 8), hair, { seed: sd + 12, lw: 2.8 });
    ctx.save(); ctx.globalAlpha = 0.55; ctx.strokeStyle = C.hairHL; ctx.lineWidth = 4; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-f * 26, -42); ctx.quadraticCurveTo(0, -52, f * 22, -44); ctx.stroke(); ctx.restore();
    G.line(ctx, [[-f * 4, -56], [-f * 8, -66], [f * 2, -62]], { color: G.tint(hair, -0.2), lw: 2.2, seed: sd + 13 });
    if (female) { ctx.fillStyle = '#E8B04A'; ctx.beginPath(); ctx.arc(ear[0], ear[1] + 14, 2.6, 0, 7); ctx.fill(); }
    if (o.sweat) { const sy = -26 + o.sweat * 18; ctx.fillStyle = '#BFE0FF'; ctx.strokeStyle = '#5A84B8'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(f * 50, sy - 9); ctx.quadraticCurveTo(f * 56, sy + 2, f * 50, sy + 5); ctx.quadraticCurveTo(f * 44, sy + 2, f * 50, sy - 9); ctx.fill(); ctx.stroke(); }
    ctx.restore(); // head
    ctx.restore();
    return { sA: [x + f * 34, y - bob - 112], sB: [x - f * 34, y - bob - 112] };
  }

  function arm(ctx, S0, Hd, f, female, seed, bend = 1) {
    const { E } = Ch.ik(S0, Hd, 62, 60, bend);
    const col = female ? C.skinW : C.blazer;
    G.limb(ctx, [S0, E, Hd], { color: col, lw: female ? 15 : 19, ink: LINE, outline: 1.6, seed });
    if (!female) { const d = [Hd[0] - E[0], Hd[1] - E[1]], n = Math.hypot(...d) || 1; G.limb(ctx, [[Hd[0] - d[0] / n * 14, Hd[1] - d[1] / n * 14], [Hd[0] - d[0] / n * 6, Hd[1] - d[1] / n * 6]], { color: '#FFFFFF', lw: 19, ink: LINE, outline: 1.4, seed: seed + 1 }); }
    paint(ctx, ell(Hd[0], Hd[1], 9.5, 8.5), female ? C.skinW : C.skinM, { seed: seed + 2, lw: 2.2 });
  }

  function wineGlass(ctx, x, y, tilt, seed) {
    // origin = the stem where the hand holds it
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt);
    const bowl = [[-15, -58], [-17, -42], [-11, -26], [0, -22], [11, -26], [17, -42], [15, -58]];
    ctx.save(); ctx.beginPath(); G.path(ctx, G.polyPts(bowl, 6), true); ctx.clip();
    ctx.rotate(-tilt); ctx.fillStyle = C.wine; ctx.globalAlpha = 0.9; ctx.fillRect(-30, -40, 60, 40); ctx.restore();
    G.shape(ctx, G.polyPts(bowl, 6), { stroke: LINE, lw: 2, seed, closed: true, fill: 'rgba(230,240,255,0.25)' });
    G.line(ctx, [[0, -22], [0, 14]], { color: LINE, lw: 2.2, seed: seed + 1, amp: 0.5 });
    G.line(ctx, [[-11, 15], [11, 15]], { color: LINE, lw: 2.4, seed: seed + 2, amp: 0.5 });
    ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-11, -54); ctx.lineTo(-12, -40); ctx.stroke();
    ctx.restore();
  }

  function table(ctx, t) {
    const top = circ(280, 280, 96, 82, 48);
    const drop = [];
    for (let i = 0; i <= 24; i++) { const a = -Math.PI / 4 + (i / 24) * Math.PI; drop.push(P(280 + 96 * Math.cos(a), 280 + 96 * Math.sin(a), 82)); }
    for (let i = 24; i >= 0; i--) { const a = -Math.PI / 4 + (i / 24) * Math.PI; drop.push(P(280 + 101 * Math.cos(a), 280 + 101 * Math.sin(a), 6 + 3 * Math.sin(i * 1.7))); }
    paint(ctx, drop, G.tint(C.cloth, -0.06), { seed: 300 });
    for (let i = 2; i < 24; i += 3) { const a = -Math.PI / 4 + (i / 24) * Math.PI; G.line(ctx, [P(280 + 96 * Math.cos(a), 280 + 96 * Math.sin(a), 78), P(280 + 101 * Math.cos(a), 280 + 101 * Math.sin(a), 12)], { color: 'rgba(150,120,140,0.4)', lw: 1.4, seed: 310 + i }); }
    paint(ctx, top, C.cloth, { seed: 301 });
  }
  function candle(ctx, t) {
    const b = P(280, 280, 82);
    paint(ctx, ell(b[0], b[1], 16, 5), '#E3B85A', { seed: 320, lw: 2 });
    paint(ctx, G.polyPts([[b[0] - 6, b[1]], [b[0] + 6, b[1]], [b[0] + 6, b[1] - 40], [b[0] - 6, b[1] - 40]], 8), C.candle, { seed: 321, lw: 2 });
    const fl = 1 + 0.18 * Math.sin(qt(t) * 23) * Math.sin(qt(t) * 7.3);
    glow(ctx, b[0], b[1] - 52, 120, 'rgba(255,190,110,0.42)');
    ctx.fillStyle = '#FFD27A'; ctx.beginPath(); ctx.ellipse(b[0], b[1] - 50, 5, 10 * fl, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#FFF6DA'; ctx.beginPath(); ctx.ellipse(b[0], b[1] - 48, 2.4, 5 * fl, 0, 0, 7); ctx.fill();
    // a single rose
    const v = P(250, 300, 82);
    paint(ctx, G.polyPts([[v[0] - 6, v[1]], [v[0] + 6, v[1]], [v[0] + 4, v[1] - 24], [v[0] - 4, v[1] - 24]], 6), '#BFD8E6', { seed: 322, lw: 1.8 });
    G.line(ctx, [[v[0], v[1] - 24], [v[0] + 2, v[1] - 44]], { color: '#4F8A5B', lw: 2, seed: 323 });
    paint(ctx, ell(v[0] + 2, v[1] - 48, 7, 6), '#D63A55', { seed: 324, lw: 1.8 });
  }
  function phoneOnTable(ctx, p, lit, shake, facedown) {
    ctx.save(); ctx.translate(p[0] + shake, p[1]); ctx.rotate(-0.35);
    paint(ctx, G.polyPts([[-18, -9], [18, -9], [18, 9], [-18, 9]], 8), '#26232E', { seed: 330, lw: 2 });
    if (!facedown) { ctx.fillStyle = lit ? '#C9C2FF' : '#1A1830'; ctx.fillRect(-15, -6.5, 30, 13); }
    ctx.restore();
    if (lit && !facedown) glow(ctx, p[0], p[1], 50, 'rgba(170,160,255,0.5)');
  }
  function phoneInHand(ctx, Hd) {
    paint(ctx, G.polyPts([[Hd[0] - 11, Hd[1] - 38], [Hd[0] + 11, Hd[1] - 38], [Hd[0] + 11, Hd[1] + 4], [Hd[0] - 11, Hd[1] + 4]], 8), '#2A2733', { seed: 340, lw: 2 });
    glow(ctx, Hd[0] - 18, Hd[1] - 24, 60, 'rgba(170,160,255,0.35)');
  }

  // ---------- poses (sampled on twos) ----------
  const W0 = P(222, 338, 48), M0 = P(338, 222, 48);   // seats left and right of the table, same depth
  const PHONE_AT = P(330, 300, 84);
  function poses(t) {
    const q = qt(t);
    const beat = S.laughBeats.reduce((a, b) => (b <= q ? b : a), -9);
    const hop = Math.exp(-(q - beat) * 7) * (q - beat < BEAT ? 1 : 0);
    const date = q < ev.stop, after = q >= ev.clink;
    const blink = S.blinks.some((b) => q >= b && q < b + 0.09);
    const laughing = date || after;
    const worriedNow = q >= ev.stop && q < ev.relief;
    const w = {
      x: W0[0], y: W0[1], f: 1, female: true, bob: laughing ? 5 * hop : 0,
      tilt: laughing ? -0.08 - 0.06 * hop : K(q, [[ev.stop, 0], [ev.stop + 0.15, 0.08], [ev.worried, 0.02], [ev.relief, 0.02], [ev.relief + 0.4, -0.05]]),
      eyes: blink ? 'closed' : laughing ? 'happy' : q >= ev.relief + 0.5 ? 'happy' : 'open',
      look: q < ev.worried && !date ? [0.6, 1] : q >= ev.grab && q < ev.relief ? [0.8, 0.6] : [1, 0],
      worry: worriedNow ? 1 : 0, raise: q >= ev.stop && q < ev.worried ? 1 : 0,
      mouth: laughing ? 'laugh' : worriedNow ? (q < ev.worried ? 'o' : 'wavy') : 'smile', open: 0.6 + 0.4 * hop, blush: after || q > ev.relief ? 1 : 0.3,
    };
    const m = {
      x: M0[0], y: M0[1], f: -1, female: false, bob: laughing ? 5 * hop : 0,
      tilt: laughing ? 0.08 + 0.06 * hop : K(q, [[ev.stop, 0], [ev.stop + 0.15, -0.1], [ev.grab, 0.04], [ev.relief, 0.06], [ev.relief + 0.4, 0.08], [ev.relief + 0.9, 0.04]]),
      eyes: blink ? 'closed' : laughing ? 'happy' : q >= ev.relief && q < ev.relief + 0.5 ? 'closed' : q >= ev.relief + 0.5 ? 'happy' : q < ev.worried ? 'wide' : 'open',
      look: q < ev.worried && !date ? [0.4, 1] : q >= ev.grab && q < ev.relief ? [0.4, 0.8] : [1, 0],
      worry: worriedNow ? 1 : 0, raise: q >= ev.stop && q < ev.worried ? 1 : 0,
      mouth: laughing ? 'laugh' : worriedNow ? (q < ev.worried ? 'o' : 'wavy') : q < ev.relief + 0.5 ? 'o' : 'smile', open: 0.5 + 0.5 * hop, blush: after ? 0.6 : 0.2,
      sweat: q >= ev.worried && q < ev.relief ? clamp((q - ev.worried) / 1.2) : 0,
    };
    // hands
    const glassUpW = [W0[0] + 70, W0[1] - 120], glassUpM = [M0[0] - 70, M0[1] - 120];
    const restW = [W0[0] + 62, W0[1] - 52], restM = [M0[0] - 62, M0[1] - 52];
    const clinkW = [540 - 18, W0[1] - 160], clinkM = [540 + 18, M0[1] - 160];
    const lift = date ? hop * 6 : 0;
    w.handA = K(q, [[0, [glassUpW[0], glassUpW[1] - lift]], [ev.stop, glassUpW], [ev.worried, restW], [ev.raise, restW], [ev.clink - 0.08, clinkW, ease.outCubic], [ev.clink + 0.4, [clinkW[0] - 8, clinkW[1] + 6]], [ev.clink + 1.2, [glassUpW[0] + 6, glassUpW[1] - 10]]]);
    m.handA = K(q, [[0, [glassUpM[0], glassUpM[1] - lift]], [ev.stop, glassUpM], [ev.worried, restM], [ev.raise, restM], [ev.clink - 0.08, clinkM, ease.outCubic], [ev.clink + 0.4, [clinkM[0] + 8, clinkM[1] + 6]], [ev.clink + 1.2, [glassUpM[0] - 6, glassUpM[1] - 10]]]);
    if (after) { w.handA = [w.handA[0], w.handA[1] - lift]; m.handA = [m.handA[0], m.handA[1] - lift]; }
    const chestW = [W0[0] + 8, W0[1] - 96];
    w.handB = K(q, [[0, [W0[0] + 20, W0[1] - 40]], [ev.worried + 0.2, [W0[0] + 20, W0[1] - 40]], [ev.worried + 0.6, chestW], [ev.relief + 1.2, chestW], [ev.relief + 1.7, [W0[0] + 20, W0[1] - 40]]]);
    const phHold = [M0[0] - 34, M0[1] - 112];
    m.handB = K(q, [[0, [M0[0] - 20, M0[1] - 40]], [ev.grab, [M0[0] - 20, M0[1] - 40]], [ev.grab + 0.25, [PHONE_AT[0] + 4, PHONE_AT[1] - 4]], [ev.phone - 0.05, phHold], [ev.relief + 0.3, phHold], [ev.relief + 0.75, [PHONE_AT[0] + 4, PHONE_AT[1] - 4]], [ev.relief + 1.1, [M0[0] - 20, M0[1] - 40]]]);
    m.phone = q >= ev.grab + 0.25 && q < ev.relief + 0.75;
    w.gTilt = q >= ev.raise && q < ev.clink + 0.4 ? 0.22 : -0.05;
    m.gTilt = q >= ev.raise && q < ev.clink + 0.4 ? -0.22 : 0.05;
    return { w, m, q };
  }

  // ---------- camera ----------
  function cam(t) {
    const q = qt(t);
    if (q < ev.worried) return { x: 540, y: K(q, [[0, 940], [0.8, 940], [ev.stop, 1000, ease.inOutCubic], [ev.worried, 1010]]), z: K(q, [[0, 1.0], [0.8, 1.0], [ev.stop, 1.55, ease.inOutCubic], [ev.stop + 0.3, 1.75, ease.outCubic], [ev.worried, 1.8]]) };
    if (q < ev.phone) return { x: 540, y: 990, z: K(q, [[ev.worried, 3.0], [ev.phone, 3.25]]) };
    if (q < ev.clink + BEAT) return { x: 540, y: K(q, [[ev.relief, 985], [ev.clink, 975]]), z: K(q, [[ev.relief, 3.1], [ev.clink, 2.8]]) };
    return { x: 540, y: K(q, [[ev.clink + BEAT, 975], [S.DURATION - 0.6, 950, ease.inOutCubic]]), z: K(q, [[ev.clink + BEAT, 2.8], [S.DURATION - 0.6, 1.0, ease.inOutCubic]]) };
  }

  function sceneRoom(ctx, t) {
    const c = cam(t), { w, m, q } = poses(t);
    ctx.save();
    ctx.translate(W / 2, H / 2); ctx.scale(c.z, c.z); ctx.translate(-c.x, -c.y);
    room(ctx, t);
    chair(ctx, W0[0], W0[1], 1, 400); chair(ctx, M0[0], M0[1], -1, 410);
    person(ctx, w); person(ctx, m);
    table(ctx, t); candle(ctx, t);
    const buzzing = S.ev.buzz.find((b) => q >= b && q < b + 0.42);
    if (!m.phone) phoneOnTable(ctx, PHONE_AT, q >= ev.stop && q < ev.relief, buzzing ? (Math.floor(q * 12) % 2 ? 2.5 : -2.5) : 0, q >= ev.relief);
    if (buzzing && !m.phone) {
      ctx.strokeStyle = '#3A2A44'; ctx.lineWidth = 2; ctx.lineCap = 'round';
      for (const s of [-1, 1]) for (const r of [24, 34]) { ctx.beginPath(); ctx.arc(PHONE_AT[0], PHONE_AT[1], r, s > 0 ? -0.5 : Math.PI - 0.5, s > 0 ? 0.5 : Math.PI + 0.5); ctx.stroke(); }
    }
    // arms over the table (the glass arm last so the glass sits in front)
    for (const p of [w, m]) {
      const sh = { sA: [p.x + p.f * 34, p.y - p.bob - 112], sB: [p.x - p.f * 34, p.y - p.bob - 112] };
      arm(ctx, sh.sB, p.handB, p.f, p.female, p.female ? 500 : 520, p.f);
      if (p.phone) phoneInHand(ctx, p.handB);
      wineGlass(ctx, p.handA[0], p.handA[1] + 8, p.gTilt, p.female ? 530 : 540);
      arm(ctx, sh.sA, p.handA, p.f, p.female, p.female ? 510 : 550, -p.f);
    }
    // the clink: a little star and rays, hearts drifting up after
    if (q >= ev.clink && q < ev.clink + 0.5) {
      const u = (q - ev.clink) / 0.5, cx = 540, cy = W0[1] - 218;
      G.star(ctx, cx, cy, 14 + 10 * (1 - u), { fill: '#FFE08A', seed: 600 });
      ctx.strokeStyle = `rgba(255,236,170,${1 - u})`; ctx.lineWidth = 2.4;
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * 18, cy + Math.sin(a) * 18); ctx.lineTo(cx + Math.cos(a) * (30 + 22 * u), cy + Math.sin(a) * (30 + 22 * u)); ctx.stroke(); }
    }
    for (const h of S.hearts) if (q >= h.t) { const u = q - h.t; G.heart(ctx, 540 + h.x + 8 * Math.sin(u * 4), W0[1] - 250 - u * 60, 0.9 + 0.2 * Math.min(u, 1), { fill: h.seed === 1 ? B.lav : '#E86A86', seed: 700 + h.seed }); }
    // lighting: warm pool from the lamp + candle, dusk at the edges
    const lp = P(280, 280, 200);
    const g = ctx.createRadialGradient(lp[0], lp[1], 40, lp[0], lp[1], 520);
    g.addColorStop(0, 'rgba(255,214,150,0.35)'); g.addColorStop(1, 'rgba(255,214,150,0)');
    ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(lp[0] - 520, lp[1] - 520, 1040, 1040);
    ctx.globalCompositeOperation = 'source-over';
    ctx.restore();
    // a warm cone of lamp light, then the dusk vignette (screen space)
    const v = ctx.createRadialGradient(W / 2, H * 0.52, H * 0.2, W / 2, H * 0.52, H * 0.75);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(30,20,60,0.45)');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
    // the hard cut onto the worried two-shot gets a one-frame flash so it reads as a hit
    if (q >= ev.worried && q < ev.worried + 1 / 12) { ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(0, 0, W, H); }
    if (q >= ev.clink && q < ev.clink + 2 / 12) { ctx.fillStyle = `rgba(255,246,220,${0.3 * (1 - (q - ev.clink) * 6)})`; ctx.fillRect(0, 0, W, H); }
  }

  // ======================= THE PHONE CLOSE-UP =======================
  function lockScreen(ctx, w, h, t) {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, '#171A40'); g.addColorStop(0.6, '#3A2585'); g.addColorStop(1, '#8C74D8');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < 30; i++) { ctx.globalAlpha = 0.3 + 0.5 * G.rnd(i, 50); ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(G.rnd(i, 51) * w, G.rnd(i, 52) * h * 0.7, 0.8 + G.rnd(i, 53), 0, 7); ctx.fill(); }
    ctx.globalAlpha = 1;
    UI.text(ctx, 'Saturday, October 31', w / 2, 112, { size: 19, weight: 700, color: '#FFFFFF', align: 'center' });
    UI.text(ctx, '8:31', w / 2, 210, { size: 96, weight: 700, color: '#FFFFFF', align: 'center', spacing: -2 });
    const q = qt(t);
    if (q < ev.notif) return;
    const p = 0.92 + 0.08 * ease.outBack(clamp((q - ev.notif) / 0.25), 2); // lands at full size on its first drawing
    ctx.save(); ctx.translate(w / 2, 300); ctx.scale(p, p); ctx.translate(-w / 2, -300);
    UI.card(ctx, 14, 246, w - 28, 330, 26, { fill: 'rgba(246,244,255,0.94)' });
    ctx.fillStyle = B.soft; ctx.beginPath(); ctx.roundRect(30, 262, 46, 46, 11); ctx.fill();
    if (logoImg) ctx.drawImage(logoImg, 30, 262, 46, 46);
    UI.text(ctx, 'AylluOS', 88, 293, { size: 19, weight: 700, color: B.ink });
    UI.text(ctx, 'now', w - 32, 293, { size: 17, weight: 400, color: '#5B6478', align: 'right' });
    UI.text(ctx, 'Baby is Sleeping', 30, 350, { size: 31, weight: 800, color: B.ink, maxW: w - 60 });
    UI.text(ctx, '8:31pm · Grandma', 30, 386, { size: 22, weight: 400, color: '#3D4660' });
    ctx.save(); ctx.beginPath(); ctx.roundRect(30, 404, w - 60, 156, 16); ctx.clip();
    ctx.fillStyle = B.soft; ctx.fillRect(30, 404, w - 60, 156);
    if (babyImg) { const iw = w - 60, ih = iw * babyImg.height / babyImg.width; ctx.drawImage(babyImg, 30, 404 - ih * 0.06, iw, ih); }
    ctx.restore();
    ctx.restore();
  }
  lockScreen.dark = true;

  function scenePhone(ctx, t) {
    const q = qt(t);
    // warm blurred restaurant behind
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#3A2240'); bg.addColorStop(0.6, '#6A3A3A'); bg.addColorStop(1, '#2A1A22');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 18; i++) glow(ctx, G.rnd(i, 60) * W, 100 + G.rnd(i, 61) * 1300, 50 + G.rnd(i, 62) * 70, i % 4 ? 'rgba(255,190,120,0.35)' : 'rgba(170,160,255,0.3)');
    const cx = SAFE.x + SAFE.w / 2 + 6 * Math.sin(q * 1.7), cy = 860 + 5 * Math.sin(q * 1.3), rot = -0.04 + 0.01 * Math.sin(q * 1.1);
    const ph = 1160;
    // forearms + palms behind the phone (indigo sleeves, white cuffs)
    for (const s of [-1, 1]) {
      const sx = cx + s * 250, sy = cy + 360;
      G.limb(ctx, [[cx + s * 520, H + 80], [cx + s * 380, sy + 260], [sx, sy]], { color: C.blazer, lw: 150, ink: LINE, outline: 3, seed: 800 + s });
      G.limb(ctx, [[sx + s * 40, sy + 60], [sx, sy]], { color: '#FFFFFF', lw: 150, ink: LINE, outline: 3, seed: 810 + s });
      paint(ctx, ell(cx + s * 262, cy + 330, 80, 170), C.skinM, { seed: 820 + s });
    }
    UI.phone(ctx, cx, cy, ph, lockScreen, t, { rot, time: '8:31', dark: true });
    // thumbs in front, low on the screen, below the notification
    for (const s of [-1, 1]) {
      const bx = cx + s * 262, by = cy + 420;
      const th = [[bx + s * 10, by + 40], [bx - s * 40, by - 40], [bx - s * 78, by - 110], [bx - s * 96, by - 150], [bx - s * 78, by - 172], [bx - s * 52, by - 150], [bx - s * 18, by - 96], [bx + s * 30, by - 30]];
      paint(ctx, G.polyPts(th, 12), C.skinM, { seed: 830 + s });
      ctx.fillStyle = 'rgba(255,236,226,0.9)'; ctx.beginPath(); ctx.ellipse(bx - s * 82, by - 150, 12, 16, s * 0.55, 0, 7); ctx.fill();
      ctx.strokeStyle = 'rgba(150,90,70,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(bx - s * 82, by - 150, 12, 16, s * 0.55, 0, 7); ctx.stroke();
    }
    glow(ctx, cx, cy - 100, 520, 'rgba(160,150,255,0.18)');
    if (q >= ev.notif && q < ev.notif + 1 / 12) glow(ctx, cx, cy - 230, 420, 'rgba(235,230,255,0.55)'); // the screen flares as it lands
    const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.75);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(20,10,30,0.5)');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  }

  globalThis.CAST = null;
  Studio.film({
    async init() {
      logoImg = await Studio.loadImage('assets/aylluos_mark.svg');
      babyImg = await Studio.loadImage('assets/baby_sleeping.png');
    },
    draw(ctx, t) {
      if (t >= ev.phone && t < ev.relief) scenePhone(ctx, t);
      else sceneRoom(ctx, t);
    },
    post: { paper: 0.6, vignette: 0.15, grain: 0.03 },
    fadeOut: 0.6,
  });
})();
