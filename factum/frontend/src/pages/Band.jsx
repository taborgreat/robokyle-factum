import React, { useEffect, useState } from 'react';
import { get, post } from '../api.js';

const NUM = [['flex_on', 'Flexor ON (V)'], ['flex_off', 'Flexor OFF (V)'], ['ext_on', 'Extensor ON (V)'], ['ext_off', 'Extensor OFF (V)'],
  ['flex_max', 'Flexor max (V)'], ['force_limit', 'Force limit (0–1)'], ['mouse_gain', 'Mouse gain'], ['mouse_deadzone', 'Mouse dead zone (°/s)'], ['mouse_accel', 'Mouse accel curve']];
const STR = [['band_id', 'Band id'], ['factum_ip', 'Factum IP'], ['factum_port', 'Factum UDP port'], ['hand_ip', 'Hand IP'], ['hand_port', 'Hand port'], ['ap_ssid', 'Hotspot name']];

export default function Band({ state }) {
  const [cfg, setCfg] = useState(null); const [err, setErr] = useState(''); const [msg, setMsg] = useState('');
  const [wifi, setWifi] = useState([]); const [apPass, setApPass] = useState(''); const [newKey, setNewKey] = useState('');
  const [cal, setCal] = useState({}); const [busy, setBusy] = useState(false);

  const load = () => get('/api/band/config').then(c => { setCfg(c); setWifi((c.wifi || []).map(w => ({ ...w, pass: '' }))); setErr(''); }).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);

  const run = async (fn, okMsg) => { setBusy(true); setMsg(''); setErr(''); try { const r = await fn(); setMsg(okMsg || 'Done'); return r; } catch (e) { setErr(e.message); } finally { setBusy(false); } };
  const save = () => run(async () => {
    const body = {};
    for (const [k] of [...NUM, ...STR]) if (cfg[k] !== undefined) body[k] = isNaN(cfg[k]) ? cfg[k] : Number(cfg[k]);
    const list = wifi.filter(w => w.ssid);
    if (list.some(w => w.pass)) body.wifi = list.map(w => ({ ssid: w.ssid, pass: w.pass }));   // a list replaces the whole list
    if (apPass) body.ap_pass = apPass;
    if (newKey) body.factum_key = newKey;
    await post('/api/band/config', body);
    if (newKey) { await fetch('/api/devices', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: newKey }) }); setNewKey(''); }
    setApPass(''); await load();
  }, 'Saved to the band');
  const calibrate = phase => run(async () => setCal(await post('/api/band/calibrate', { phase })), phase === 'apply' ? 'Thresholds applied' : `Capturing ${phase} for 10 s — hold it`);

  if (err && !cfg) return <div className="panel"><h2>Band</h2><p className="msg err">{err}</p><p className="msg">Settings can only be changed while the band is in HAND-FACTUM mode on the home network.</p><button className="btn secondary" onClick={load}>Retry</button></div>;
  if (!cfg) return <div className="panel"><p className="msg">Loading…</p></div>;
  const have = cal.have || 0;
  return (
    <>
      <div className="grid">
        <div className="panel">
          <h2>Thresholds &amp; mouse</h2>
          <div className="form">{NUM.map(([k, l]) => <div className="row" key={k}><label htmlFor={k}>{l}</label><input id={k} type="number" step="0.001" value={cfg[k] ?? ''} onChange={e => setCfg({ ...cfg, [k]: e.target.value })} /></div>)}</div>
        </div>
        <div className="panel">
          <h2>Calibrate</h2>
          <p className="msg">Each capture takes 10 s. Rest = arm relaxed. Close = steady fist. Open = fingers spread hard. Apply sets ON at 40 % and OFF at 25 % of the range.</p>
          <div className="steps">
            {[['rest', 1, 'Rest'], ['close', 2, 'Close'], ['open', 4, 'Open']].map(([p, bit, l], i) => (
              <div className={`step ${have & bit ? 'done' : ''}`} key={p}><span className="n">{i + 1}</span><span>{l}</span><button className="btn secondary" disabled={busy} onClick={() => calibrate(p)}>Capture</button></div>))}
            <div className={`step ${have === 7 ? '' : ''}`}><span className="n">4</span><span>Apply thresholds</span><button className="btn" disabled={busy || have !== 7} onClick={() => calibrate('apply')}>Apply</button></div>
          </div>
          {cal.rest && <p className="msg mono">rest {cal.rest.map(v => v.toFixed(3)).join('/')} · close {cal.close?.toFixed(3)} · open {cal.open?.toFixed(3)}</p>}
        </div>
        <div className="panel">
          <h2>Network</h2>
          <div className="form">
            {STR.map(([k, l]) => <div className="row" key={k}><label htmlFor={k}>{l}</label><input id={k} value={cfg[k] ?? ''} onChange={e => setCfg({ ...cfg, [k]: e.target.value })} /></div>)}
            <div className="row"><label htmlFor="ap_pass">Hotspot password</label><input id="ap_pass" type="password" value={apPass} placeholder="unchanged" onChange={e => setApPass(e.target.value)} /></div>
          </div>
          <h3 style={{ margin: '14px 0 6px' }}>Wi-Fi networks, tried in order</h3>
          <p className="msg">Passwords never come back from the band. To change the list, fill in every password and save.</p>
          <div className="form">{[0, 1, 2, 3].map(i => <div className="row" key={i}><input aria-label={`SSID ${i + 1}`} placeholder={`network ${i + 1}`} value={wifi[i]?.ssid || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), ssid: e.target.value }; setWifi(w); }} /><input aria-label={`password ${i + 1}`} type="password" placeholder="password" value={wifi[i]?.pass || ''} onChange={e => { const w = [...wifi]; w[i] = { ...(w[i] || {}), pass: e.target.value }; setWifi(w); }} /></div>)}</div>
        </div>
        <div className="panel">
          <h2>Actions</h2>
          <div className="actions">
            <button className="btn secondary" disabled={busy} onClick={() => run(() => post('/api/band/buzz', { ms: 150 }), 'Buzzed')}>Buzz</button>
            {['HAND-FACTUM', 'HAND-DIRECT', 'MOUSE'].map((m, i) => <button key={m} className="btn secondary" disabled={busy} onClick={() => run(() => post('/api/band/mode', { mode: i }), `Mode → ${m}`)}>{m}</button>)}
          </div>
          <h3 style={{ margin: '14px 0 6px' }}>Shared key</h3>
          <p className="msg">Factum sends this on every write. Setting a new one updates the band and Factum together. {state.devices?.keySet ? 'A custom key is set.' : 'Still the factory default — change it.'}</p>
          <input aria-label="New shared key" type="password" placeholder="new key" value={newKey} onChange={e => setNewKey(e.target.value)} />
        </div>
      </div>
      <div className="actions"><button className="btn" disabled={busy} onClick={save}>Save to band</button>{msg && <span className="msg ok">{msg}</span>}{err && <span className="msg err">{err}</span>}</div>
    </>
  );
}
