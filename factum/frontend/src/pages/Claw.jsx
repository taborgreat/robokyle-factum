import React, { useEffect, useState } from 'react';
import { get, post } from '../api.js';

const NUM = [['pos_open', 'Open position (0–4095)'], ['pos_closed', 'Closed position'], ['torque_min', 'Preview torque (0–1000)'], ['torque_max', 'Max torque'], ['speed', 'Speed']];

// Kyle's claw: the hand we are building. Until it is on the network this page says so; once it answers Factum the
// settings below are live. Its virtual twin (a 3D claw driven by the same relay) is next, in the place of the banner.
export default function Claw({ state }) {
  const [cfg, setCfg] = useState(null); const [err, setErr] = useState(''); const [msg, setMsg] = useState(''); const [wifi, setWifi] = useState([]);
  const load = () => get('/api/hand/config').then(c => { setCfg(c); setWifi((c.wifi || []).map(w => ({ ...w, pass: '' }))); setErr(''); }).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);
  const hs = state.status?.hand; const v = state.status?.virtual;
  const save = async () => {
    setMsg(''); setErr('');
    try {
      const body = {}; for (const [k] of NUM) body[k] = Number(cfg[k]);
      body.hand_id = cfg.hand_id;
      const list = wifi.filter(w => w.ssid); if (list.some(w => w.pass)) body.wifi = list.map(w => ({ ssid: w.ssid, pass: w.pass }));
      await post('/api/hand/config', body); setMsg('Saved to the claw'); await load();
    } catch (e) { setErr(e.message); }
  };
  return (
    <>
      <div className="panel wide">
        <h2>Claw <span className="pill warn">coming soon</span></h2>
        <p className="msg">The claw is Kyle's own hand, built here: one servo, a grip you can see through, the band's protocol on its Wi-Fi. This page is where it will be watched and tuned, and a virtual claw will stand in for it while it is built and tested, the way the virtual Brunel does on the Brunel page. Until the claw answers Factum, nothing below is live.</p>
        <p className="msg mono">{hs ? `claw online: pos ${hs.pos} · load ${hs.load} · grip ${hs.grip} · servo ${hs.servo ? 'ok' : 'MISSING'}` : `claw offline${state.status?.handErr ? ` (${state.status.handErr})` : ''} · relay target: ${v?.target || 'virtual'}`}</p>
      </div>
      {cfg ? (
        <>
          <div className="grid">
            <div className="panel">
              <h2>Servo</h2>
              <p className="msg">Set the end positions with the claw assembled: read <span className="mono">pos</span> above while moving it by hand with torque off.</p>
              <div className="form">
                <div className="row"><label htmlFor="hand_id">Claw id</label><input id="hand_id" value={cfg.hand_id || ''} onChange={e => setCfg({ ...cfg, hand_id: e.target.value })} /></div>
                {NUM.map(([k, l]) => <div className="row" key={k}><label htmlFor={k}>{l}</label><input id={k} type="number" value={cfg[k] ?? ''} onChange={e => setCfg({ ...cfg, [k]: e.target.value })} /></div>)}
              </div>
            </div>
            <div className="panel">
              <h2>Wi-Fi, tried in order</h2>
              <p className="msg">The network Factum is on first, the band's hotspot second. Fill in every password to change the list.</p>
              <div className="form">{[0, 1, 2, 3].map(i => <div className="row" key={i}><input aria-label={`SSID ${i + 1}`} placeholder={`network ${i + 1}`} value={wifi[i]?.ssid || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), ssid: e.target.value }; setWifi(w); }} /><input aria-label={`password ${i + 1}`} type="password" placeholder="password" value={wifi[i]?.pass || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), pass: e.target.value }; setWifi(w); }} /></div>)}</div>
            </div>
          </div>
          <div className="actions"><button className="btn" onClick={save}>Save to claw</button>{msg && <span className="msg ok">{msg}</span>}{err && <span className="msg err">{err}</span>}</div>
        </>
      ) : (
        <div className="panel"><p className="msg">Settings appear here once the claw answers Factum.{err ? ` (${err})` : ''}</p><button className="btn secondary" onClick={load}>Try again</button></div>
      )}
    </>
  );
}
