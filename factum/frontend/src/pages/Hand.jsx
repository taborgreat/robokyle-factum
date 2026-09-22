import React, { useEffect, useState } from 'react';
import { get, post } from '../api.js';

const NUM = [['pos_open', 'Open position (0–4095)'], ['pos_closed', 'Closed position'], ['torque_min', 'Preview torque (0–1000)'], ['torque_max', 'Max torque'], ['speed', 'Speed']];

export default function Hand({ state }) {
  const [cfg, setCfg] = useState(null); const [err, setErr] = useState(''); const [msg, setMsg] = useState(''); const [wifi, setWifi] = useState([]);
  const load = () => get('/api/hand/config').then(c => { setCfg(c); setWifi((c.wifi || []).map(w => ({ ...w, pass: '' }))); setErr(''); }).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);
  const hs = state.status?.hand;
  const save = async () => {
    setMsg(''); setErr('');
    try {
      const body = {}; for (const [k] of NUM) body[k] = Number(cfg[k]);
      body.hand_id = cfg.hand_id;
      const list = wifi.filter(w => w.ssid); if (list.some(w => w.pass)) body.wifi = list.map(w => ({ ssid: w.ssid, pass: w.pass }));
      await post('/api/hand/config', body); setMsg('Saved to the hand'); await load();
    } catch (e) { setErr(e.message); }
  };
  if (err && !cfg) return <div className="panel"><h2>Hand</h2><p className="msg err">{err}</p><button className="btn secondary" onClick={load}>Retry</button></div>;
  if (!cfg) return <div className="panel"><p className="msg">Loading…</p></div>;
  return (
    <>
      <div className="grid">
        <div className="panel">
          <h2>Servo</h2>
          <p className="msg">Set the end positions with the claw assembled: read <span className="mono">pos</span> below while moving it by hand with torque off.</p>
          <p className="msg mono">{hs ? `now: pos ${hs.pos} · load ${hs.load} · grip ${hs.grip} · servo ${hs.servo ? 'ok' : 'MISSING'}` : 'hand offline'}</p>
          <div className="form">
            <div className="row"><label htmlFor="hand_id">Hand id</label><input id="hand_id" value={cfg.hand_id || ''} onChange={e => setCfg({ ...cfg, hand_id: e.target.value })} /></div>
            {NUM.map(([k, l]) => <div className="row" key={k}><label htmlFor={k}>{l}</label><input id={k} type="number" value={cfg[k] ?? ''} onChange={e => setCfg({ ...cfg, [k]: e.target.value })} /></div>)}
          </div>
        </div>
        <div className="panel">
          <h2>Wi-Fi, tried in order</h2>
          <p className="msg">Home network first, the band's hotspot second. Fill in every password to change the list.</p>
          <div className="form">{[0, 1, 2, 3].map(i => <div className="row" key={i}><input aria-label={`SSID ${i + 1}`} placeholder={`network ${i + 1}`} value={wifi[i]?.ssid || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), ssid: e.target.value }; setWifi(w); }} /><input aria-label={`password ${i + 1}`} type="password" placeholder="password" value={wifi[i]?.pass || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), pass: e.target.value }; setWifi(w); }} /></div>)}</div>
        </div>
      </div>
      <div className="actions"><button className="btn" onClick={save}>Save to hand</button>{msg && <span className="msg ok">{msg}</span>}{err && <span className="msg err">{err}</span>}</div>
    </>
  );
}
