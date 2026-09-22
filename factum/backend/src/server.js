// Factum: listener for the band's frames + the only writer of device settings. Serves the React app.
//   GET  /api/state                     everything the dashboard needs (stats, device status, devices)
//   GET  /api/frames?n=500              recent frames
//   GET  /api/logs  /api/logs/:file     daily JSONL logs
//   GET  /api/devices  PUT /api/devices IPs and the shared key (key is write-only from the UI)
//   GET  /api/:dev/status               proxied, no key needed
//   GET  /api/:dev/config               proxied with the key
//   POST /api/:dev/config {partial}     merge into the device's flash config
//   POST /api/band/calibrate|buzz|mode|lights  proxied band actions
//   WS   /ws                            {type:'frame'} live frames, {type:'status'} device status
import express from 'express';
import http from 'node:http';
import path from 'node:path';
import fs from 'node:fs';
import { WebSocketServer } from 'ws';
import { PORT, POLL_MS, DATA_DIR } from './config.js';
import { devices, update, call } from './devices.js';
import * as ingest from './ingest.js';

const app = express();
app.use(express.json({ limit: '64kb' }));

const status = { band: null, hand: null, bandAt: 0, handAt: 0, bandErr: '', handErr: '' };

function publicDevices() {
  const { key, ...rest } = devices;
  return { ...rest, keySet: key !== 'change-me-on-first-setup' };
}

app.get('/api/state', (req, res) => res.json({ stats: ingest.stats, status, devices: publicDevices(), last: ingest.ring.at(-1) || null }));
app.get('/api/frames', (req, res) => { const n = Math.min(Number(req.query.n) || 500, ingest.ring.length); res.json(ingest.ring.slice(-n)); });
app.get('/api/logs', (req, res) => res.json(ingest.logFiles()));
app.get('/api/logs/:file', (req, res) => {
  const f = path.join(DATA_DIR, path.basename(req.params.file));
  if (!fs.existsSync(f)) return res.status(404).end();
  res.type('application/x-ndjson').sendFile(f);
});
app.get('/api/devices', (req, res) => res.json(publicDevices()));
app.put('/api/devices', (req, res) => { update(req.body || {}); res.json(publicDevices()); });

const DEV = /^(band|hand)$/;
const proxy = (fn) => async (req, res) => {
  if (!DEV.test(req.params.dev)) return res.status(404).json({ error: 'unknown device' });
  try { res.json(await fn(req)); }
  catch (e) { res.status(e.status || 502).json({ error: e.message, body: e.body }); }
};
app.get('/api/:dev/status', proxy(req => call(req.params.dev, 'GET', '/status')));
app.get('/api/:dev/config', proxy(req => call(req.params.dev, 'GET', '/config')));
app.post('/api/:dev/config', proxy(req => call(req.params.dev, 'POST', '/config', req.body)));
for (const action of ['calibrate', 'buzz', 'mode', 'lights']) {
  app.post(`/api/band/${action}`, proxy(req => call('band', 'POST', `/${action}`, req.body)));
}
app.post('/api/band/lights/preview', proxy(req => call('band', 'POST', '/lights/preview', req.body)));

// frontend build, when present
const dist = new URL('../../frontend/dist/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
if (fs.existsSync(dist)) {
  app.use(express.static(dist));
  app.get(/^(?!\/api|\/ws).*/, (req, res) => res.sendFile(path.join(dist, 'index.html')));
}

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });
function broadcast(obj) { const s = JSON.stringify(obj); for (const c of wss.clients) if (c.readyState === 1) c.send(s); }
wss.on('connection', ws => ws.send(JSON.stringify({ type: 'hello', status, devices: publicDevices(), recent: ingest.ring.slice(-500) })));
ingest.subscribe(f => broadcast({ type: 'frame', frame: f }));

// poll both devices' /status so the dashboard shows them even when no frames flow (mouse mode, hand idle)
async function poll(which) {
  try { status[which] = await call(which, 'GET', '/status'); status[`${which}At`] = Date.now(); status[`${which}Err`] = ''; }
  catch (e) { status[`${which}Err`] = e.message; }
}
setInterval(async () => { await Promise.all([poll('band'), poll('hand')]); broadcast({ type: 'status', status, stats: ingest.stats }); }, POLL_MS);

ingest.start();
server.listen(PORT, () => console.log(`factum: http://localhost:${PORT}  (data in ${DATA_DIR})`));
