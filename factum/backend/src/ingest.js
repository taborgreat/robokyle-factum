// UDP frame ingest: every packet from the band is parsed, kept in a ring, logged to a daily JSONL file, and
// pushed to the live subscribers (the dashboard, and the relay that drives the hand from the frame's `h`).
import dgram from 'node:dgram';
import fs from 'node:fs';
import path from 'node:path';
import { UDP_PORT, DATA_DIR, RING_SIZE } from './config.js';
import { learnBandIp } from './devices.js';

export const ring = [];                       // most recent last
export const stats = { frames: 0, dropped: 0, lastSeq: null, lastAt: 0, rate: 0, estops: [] };
const subscribers = new Set();
let logStream, logDay = '';

function logFrame(f) {
  const day = new Date().toISOString().slice(0, 10);
  if (day !== logDay) {
    logStream?.end();
    fs.mkdirSync(DATA_DIR, { recursive: true });
    logStream = fs.createWriteStream(path.join(DATA_DIR, `frames-${day}.jsonl`), { flags: 'a' });
    logDay = day;
  }
  logStream.write(JSON.stringify(f) + '\n');
}

export function subscribe(fn) { subscribers.add(fn); return () => subscribers.delete(fn); }
export function noteEstop(f) { stats.estops.unshift({ at: Date.now(), seq: f.seq ?? null, via: f.via || 'udp' }); stats.estops.length = Math.min(stats.estops.length, 20); }

export function start() {
  const sock = dgram.createSocket('udp4');
  sock.on('message', (msg, rinfo) => {
    let f;
    try { f = JSON.parse(msg.toString()); } catch { stats.dropped++; return; }
    f.rx = Date.now(); f.from = rinfo.address;
    learnBandIp(rinfo.address);
    if (f.estop) noteEstop(f);
    if (stats.lastSeq !== null && typeof f.seq === 'number' && f.seq > stats.lastSeq + 1) stats.dropped += f.seq - stats.lastSeq - 1;
    stats.lastSeq = typeof f.seq === 'number' ? f.seq : stats.lastSeq;
    stats.frames++; stats.lastAt = f.rx;
    ring.push(f); if (ring.length > RING_SIZE) ring.shift();
    logFrame(f);
    for (const fn of subscribers) fn(f);
  });
  sock.on('listening', () => console.log(`ingest: udp/${UDP_PORT}`));
  sock.bind(UDP_PORT);
  // frame rate over the last second
  setInterval(() => { const t = Date.now() - 1000; stats.rate = ring.filter(f => f.rx > t).length; }, 1000);
}

export function logFiles() {
  try { return fs.readdirSync(DATA_DIR).filter(n => n.startsWith('frames-')).sort().reverse(); } catch { return []; }
}
