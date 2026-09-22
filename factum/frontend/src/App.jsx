import React, { useEffect, useState, useRef } from 'react';
import { connect, get } from './api.js';
import Live from './pages/Live.jsx';
import Band from './pages/Band.jsx';
import Hand from './pages/Hand.jsx';
import Devices from './pages/Devices.jsx';

const PAGES = { live: 'Live', band: 'Band', hand: 'Hand', devices: 'Devices' };

export default function App() {
  const [page, setPage] = useState(location.hash.slice(1) || 'live');
  const [state, setState] = useState({ status: {}, stats: {}, devices: {} });
  const [frames, setFrames] = useState([]);
  const buf = useRef([]);

  useEffect(() => { location.hash = page; }, [page]);
  useEffect(() => {
    get('/api/state').then(s => setState(s)).catch(() => {});
    const stop = connect(m => {
      if (m.type === 'hello') { buf.current = m.recent || []; setFrames(buf.current.slice()); setState(s => ({ ...s, status: m.status, devices: m.devices })); }
      else if (m.type === 'frame') { buf.current.push(m.frame); if (buf.current.length > 1500) buf.current.shift(); }
      else if (m.type === 'status') setState(s => ({ ...s, status: m.status, stats: m.stats }));
    });
    const t = setInterval(() => setFrames(buf.current.slice()), 100);     // 10 Hz repaint is plenty
    return () => { stop(); clearInterval(t); };
  }, []);

  const last = frames.at(-1);
  const bandLive = last && Date.now() - last.rx < 1500;
  const bandUp = !!state.status?.band && !state.status?.bandErr;
  const handUp = !!state.status?.hand && !state.status?.handErr;

  return (
    <>
      <header className="topbar">
        <div className="brand"><i /><h1>Factum</h1></div>
        <span className="link"><i className={bandLive ? 'on' : bandUp ? 'on' : 'bad'} />band {bandLive ? 'streaming' : bandUp ? 'reachable' : 'offline'}</span>
        <span className="link"><i className={handUp ? 'on' : 'bad'} />hand {handUp ? 'reachable' : 'offline'}</span>
        <nav>{Object.entries(PAGES).map(([k, v]) => <button key={k} className={page === k ? 'on' : ''} onClick={() => setPage(k)}>{v}</button>)}</nav>
      </header>
      <main>
        {page === 'live' && <Live frames={frames} state={state} />}
        {page === 'band' && <Band state={state} />}
        {page === 'hand' && <Hand state={state} />}
        {page === 'devices' && <Devices state={state} onChange={d => setState(s => ({ ...s, devices: d }))} />}
      </main>
    </>
  );
}
