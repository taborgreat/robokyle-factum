import React, { useState } from 'react';
import { put, get } from '../api.js';

export default function Devices({ state, onChange }) {
  const d = state.devices || {}; const [band, setBand] = useState(d.band?.ip || ''); const [hand, setHand] = useState(d.hand?.ip || ''); const [key, setKey] = useState(''); const [msg, setMsg] = useState(''); const [logs, setLogs] = useState(null);
  const save = async () => { const body = { band: { ip: band }, hand: { ip: hand } }; if (key) body.key = key; onChange(await put('/api/devices', body)); setKey(''); setMsg('Saved'); };
  const when = t => t ? new Date(t).toLocaleTimeString() : 'never';
  return (
    <div className="grid">
      <div className="panel">
        <h2>Where things are</h2>
        <p className="msg">The band's IP is learned from its frames automatically. Both devices answer on port 80 on the LAN.</p>
        <div className="form">
          <div className="row"><label htmlFor="band_ip">Band IP</label><input id="band_ip" value={band} onChange={e => setBand(e.target.value)} placeholder="learned from frames" /></div>
          <div className="row"><label>Band last seen</label><span className="mono">{when(d.band?.lastSeen)}</span></div>
          <div className="row"><label htmlFor="hand_ip">Hand IP</label><input id="hand_ip" value={hand} onChange={e => setHand(e.target.value)} placeholder="e.g. 192.168.1.11" /></div>
          <div className="row"><label htmlFor="key">Shared key (Factum side only)</label><input id="key" type="password" value={key} onChange={e => setKey(e.target.value)} placeholder={d.keySet ? 'set' : 'factory default'} /></div>
        </div>
        <div className="actions" style={{ marginTop: 10 }}><button className="btn" onClick={save}>Save</button>{msg && <span className="msg ok">{msg}</span>}</div>
      </div>
      <div className="panel">
        <h2>Frame logs</h2>
        <p className="msg">Every frame is logged from the first session, one JSONL file per day, in the backend's data folder.</p>
        <button className="btn secondary" onClick={() => get('/api/logs').then(setLogs)}>List</button>
        {logs && <ul>{logs.map(f => <li key={f}><a href={`/api/logs/${f}`}>{f}</a></li>)}{logs.length === 0 && <li className="msg">none yet</li>}</ul>}
      </div>
    </div>
  );
}
