// Factum: listener for the band's frames, the only writer of device settings, and in HAND-FACTUM the hand's
// commander: the virtual Brunel hand lives here at /brunel (viewer + Open Bionics API) and the relay drives it,
// or the claw, from the frame's `h`. Serves the React app.
//   /brunel/                            virtual Brunel hand: viewer; its API under it (POST /brunel/gesture/execute ...)
//   POST /band/estop                    the band's own ESTOP post ({factum_path}/estop)
//   GET  /api/state                     everything the dashboard needs (stats, device status, devices)
//   GET  /api/frames?n=500              recent frames
//   GET  /api/logs  /api/logs/:file     daily JSONL logs
//   GET  /api/devices  PUT /api/devices IPs and the shared key (key is write-only from the UI)
//   GET  /api/:dev/status               proxied, no key needed
//   GET  /api/:dev/config               proxied with the key
//   POST /api/:dev/config {partial}     merge into the device's flash config
//   POST /api/band/calibrate|buzz|mode|lights  proxied band actions
//   WS   /ws                            {type:'frame'} live frames, {type:'status'} device status, {type:'hand'} virtual hand
import express from 'express';
import http from 'node:http';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { WebSocketServer } from 'ws';
import { PORT, POLL_MS, DATA_DIR } from './config.js';
import { devices, update, call } from './devices.js';
import * as ingest from './ingest.js';
import { createBrunelHand } from '../../brunel/index.js';
import { createRelay } from './relay.js';

const app = express();

// ---- the virtual Brunel hand at /brunel/: the viewer, and the Open Bionics API under it. Mounted ahead of the JSON
// middleware because it reads its own request bodies and answers CORS the way the real device does. Express strips
// the prefix, so the package sees the spec's paths. three.js comes from this backend's node_modules.
const THREE_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.resolve('three'))));
const brunel = createBrunelHand({ storePath: path.join(DATA_DIR, 'brunel-eeprom.json'), threeDir: THREE_DIR });
const relay = createRelay(brunel.hand);
app.use('/brunel', (req, res) => {
  if (req.url === '/' && !req.originalUrl.startsWith('/brunel/')) return res.redirect(302, '/brunel/');   // page-relative URLs need the slash
  brunel.handle(req, res);
});

app.use(express.json({ limit: '64kb' }));

// the band's ESTOP post: POST {factum_path}/estop (default /band/estop), body {id, seq, t, estop: true}. The same
// event also arrives as five UDP frames; both land in the ESTOP log and stop the hand.
app.post('/band/estop', (req, res) => { ingest.noteEstop({ ...(req.body || {}), via: 'http' }); relay.estop('http'); res.json({ ok: true }); });

const status = { band: null, hand: null, bandAt: 0, handAt: 0, bandErr: '', handErr: '' };

function publicDevices() {
  const { key, ...rest } = devices;
  return { ...rest, keySet: key !== 'change-me-on-first-setup' };
}

app.get('/api/state', (req, res) => res.json({ stats: ingest.stats, status: { ...status, virtual: relay.view() }, devices: publicDevices(), last: ingest.ring.at(-1) || null }));
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
  app.get(/^(?!\/api|\/ws|\/brunel|\/band\/).*/, (req, res) => res.sendFile(path.join(dist, 'index.html')));
}

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });
function broadcast(obj) { const s = JSON.stringify(obj); for (const c of wss.clients) if (c.readyState === 1) c.send(s); }
wss.on('connection', ws => ws.send(JSON.stringify({ type: 'hello', status: { ...status, virtual: relay.view() }, devices: publicDevices(), recent: ingest.ring.slice(-500) })));
ingest.subscribe(f => broadcast({ type: 'frame', frame: f }));
ingest.subscribe(f => relay.onFrame(f));                                     // HAND-FACTUM: the frame's `h` drives the hand
brunel.hand.on('state', () => broadcast({ type: 'hand', state: relay.view() }));

// poll both devices' /status so the dashboard shows them even when no frames flow (mouse mode, hand idle)
async function poll(which) {
  try { status[which] = await call(which, 'GET', '/status'); status[`${which}At`] = Date.now(); status[`${which}Err`] = ''; }
  catch (e) { status[`${which}Err`] = e.message; }
}
setInterval(async () => { await Promise.all([poll('band'), poll('hand')]); status.virtual = relay.view(); broadcast({ type: 'status', status, stats: ingest.stats }); }, POLL_MS);

ingest.start();
server.listen(PORT, () => console.log(`factum: http://localhost:${PORT}  (data in ${DATA_DIR}; virtual Brunel at /brunel/)`));
