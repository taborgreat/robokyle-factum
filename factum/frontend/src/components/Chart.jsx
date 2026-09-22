import React, { useEffect, useRef } from 'react';
// Effort strip chart on a canvas: flexor green, extensor yellow, threshold lines from the band config when known.
export default function Chart({ frames, thresholds, seconds = 20 }) {
  const ref = useRef();
  useEffect(() => {
    const c = ref.current, ctx = c.getContext('2d');
    const W = c.width = c.clientWidth * devicePixelRatio, H = c.height = 220 * devicePixelRatio;
    ctx.clearRect(0, 0, W, H);
    const now = Date.now(), t0 = now - seconds * 1000, yMax = 1.0;
    const x = t => ((t - t0) / (seconds * 1000)) * W, y = v => H - (Math.min(v, yMax) / yMax) * (H - 10);
    ctx.strokeStyle = '#D3DBD7'; ctx.lineWidth = 1;
    for (let v = 0.25; v < yMax; v += 0.25) { ctx.beginPath(); ctx.moveTo(0, y(v)); ctx.lineTo(W, y(v)); ctx.stroke(); }
    const line = (key, color, idx) => {
      ctx.strokeStyle = color; ctx.lineWidth = 2 * devicePixelRatio; ctx.beginPath(); let started = false;
      for (const f of frames) { if (!f.c || f.rx < t0) continue; const px = x(f.rx), py = y(f.c[idx]); started ? ctx.lineTo(px, py) : ctx.moveTo(px, py); started = true; }
      ctx.stroke();
    };
    line('flex', '#154733', 0); line('ext', '#D9B10E', 1);
    if (thresholds) {
      ctx.setLineDash([6, 6]); ctx.lineWidth = 1.5 * devicePixelRatio;
      for (const [k, col] of [['flex_on', '#154733'], ['ext_on', '#D9B10E']]) { if (thresholds[k] == null) continue; ctx.strokeStyle = col; ctx.beginPath(); ctx.moveTo(0, y(thresholds[k])); ctx.lineTo(W, y(thresholds[k])); ctx.stroke(); }
      ctx.setLineDash([]);
    }
    ctx.fillStyle = '#5E6B66'; ctx.font = `${11 * devicePixelRatio}px JetBrains Mono, monospace`;
    for (let v = 0.25; v < yMax; v += 0.25) ctx.fillText(v.toFixed(2) + ' V', 4 * devicePixelRatio, y(v) - 3);
  }, [frames, thresholds, seconds]);
  return <canvas ref={ref} style={{ height: 220 }} aria-label="Effort chart, flexor green and extensor yellow" />;
}
