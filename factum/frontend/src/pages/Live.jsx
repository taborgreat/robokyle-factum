import React, { useEffect, useState } from 'react';
import Chart from '../components/Chart.jsx';
import { get } from '../api.js';

const MODES = ['HAND-FACTUM', 'HAND-DIRECT', 'MOUSE', 'HAND-WIRED'];
const INTENT = ['rest', 'close', 'open', 'co-contraction'];

export default function Live({ frames, state }) {
  const last = frames.at(-1); const bs = state.status?.band; const hs = state.status?.hand; const st = state.stats || {};
  const [cfg, setCfg] = useState(null);
  useEffect(() => { get('/api/band/config').then(setCfg).catch(() => {}); }, [state.status?.bandAt && Math.floor(state.status.bandAt / 60000)]);
  const pct = v => v == null ? '–' : Math.round(v);
  return (
    <>
      <div className="grid">
        <div className="panel stat"><span className="k">frames / s</span><span className="v">{st.rate ?? 0}</span><span className="s">{st.frames ?? 0} total · {st.dropped ?? 0} gaps</span></div>
        <div className="panel stat"><span className="k">mode</span><span className="v">{bs ? MODES[bs.mode] ?? bs.mode : '–'}</span><span className="s">{bs?.wired ? 'cord in' : bs ? `${bs.ip} · ${bs.rssi} dBm` : state.status?.bandErr || 'no band'}</span></div>
        <div className="panel stat"><span className="k">battery</span><span className="v">{bs ? `${bs.pct} %` : last?.b ? `${last.b.toFixed(2)} V` : '–'}</span><span className="s">{bs ? `${bs.battery.toFixed(2)} V` : ''}</span></div>
        <div className="panel stat"><span className="k">intent</span><span className="v">{last ? INTENT[last.i] ?? '–' : '–'}</span><span className="s">{last ? `flex ${last.c[0].toFixed(3)} · ext ${last.c[1].toFixed(3)} V` : ''}</span></div>
        <div className="panel stat"><span className="k">orientation</span><span className="v mono" style={{ fontSize: '1.2rem' }}>{last?.o ? last.o.map(v => pct(v)).join(' / ') : '–'}</span><span className="s">yaw / pitch / roll · {bs?.imu ? 'IMU ok' : 'IMU missing'}</span></div>
        <div className="panel stat"><span className="k">hand</span><span className="v">{hs ? hs.grip : '–'}</span><span className="s">{hs ? `pos ${hs.pos} · load ${hs.load} · ${hs.estop ? 'ESTOP' : hs.closing ? 'closing' : 'idle'}` : state.status?.handErr || 'no hand'}</span></div>
      </div>
      <div className="panel wide">
        <h2>Effort, last 20 s</h2>
        <Chart frames={frames} thresholds={cfg} />
        <div className="msg" style={{ marginTop: 6 }}>Dashed lines are the band's ON thresholds. Rest should sit well under them; a fist should cross the green one cleanly.</div>
      </div>
      {st.estops?.length > 0 && <div className="panel wide"><h2>ESTOP events</h2><table><thead><tr><th>when</th><th>seq</th></tr></thead><tbody>{st.estops.map(e => <tr key={e.at}><td>{new Date(e.at).toLocaleString()}</td><td className="mono">{e.seq}</td></tr>)}</tbody></table></div>}
    </>
  );
}
