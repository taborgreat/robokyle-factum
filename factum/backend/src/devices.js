// Device registry: where the band and the hand live and the shared key. Persisted in data/devices.json.
// The band's IP is learned from its UDP frames; the hand's is entered on the site (or learned from /status later).
import fs from 'node:fs';
import path from 'node:path';
import { DATA_DIR, DEVICE_TIMEOUT_MS } from './config.js';

const FILE = path.join(DATA_DIR, 'devices.json');
const DEFAULTS = {
  key: 'change-me-on-first-setup',
  band: { ip: '', port: 80, id: 'band1', lastSeen: 0 },
  hand: { ip: '', port: 80, id: 'claw1', lastSeen: 0 },
};

export let devices = load();

function load() {
  try { return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(FILE, 'utf8')) }; }
  catch { return structuredClone(DEFAULTS); }
}
export function save() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify(devices, null, 2));
}
export function update(patch) {
  devices = { ...devices, ...patch, band: { ...devices.band, ...(patch.band || {}) }, hand: { ...devices.hand, ...(patch.hand || {}) } };
  save();
  return devices;
}
export function learnBandIp(ip) {
  if (devices.band.ip !== ip) { devices.band.ip = ip; save(); }
  devices.band.lastSeen = Date.now();
}

// Talk to a device. Factum is the only thing that carries the key; the frontend never sees it.
export async function call(which, method, route, body) {
  const d = devices[which];
  if (!d?.ip) throw Object.assign(new Error(`${which}: no IP known yet`), { status: 503 });
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), DEVICE_TIMEOUT_MS);
  try {
    const res = await fetch(`http://${d.ip}:${d.port}${route}`, {
      method, signal: ctrl.signal,
      headers: { 'Content-Type': 'application/json', 'X-Factum-Key': devices.key },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await res.text();
    let json; try { json = JSON.parse(text); } catch { json = { raw: text }; }
    if (!res.ok) throw Object.assign(new Error(json.error || `${which} answered ${res.status}`), { status: res.status, body: json });
    return json;
  } catch (e) {
    if (e.name === 'AbortError') throw Object.assign(new Error(`${which} at ${d.ip} did not answer`), { status: 504 });
    throw e;
  } finally { clearTimeout(t); }
}
