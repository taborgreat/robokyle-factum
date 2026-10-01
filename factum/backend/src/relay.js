// HAND-FACTUM adapter. The band never addresses the hand over Wi-Fi: every frame carries `h`, the command it would
// have sent ({cmd, a}: open | close {force} | grip {name, preview} | stop | estop | keepalive). Factum applies it to
// the virtual Brunel hand mounted at /brunel (always, unless the relay target is the claw alone) and, when the target
// includes the claw, forwards it to the real hand over the band's own protocol (POST /open, /close, /grip ...) and
// keeps the claw's watchdog fed while frames flow. The band repeats its last command in every frame, so a command is
// applied once, when it changes; a command the virtual hand refuses mid-motion is retried until it lands or is replaced.
import { devices, call } from './devices.js';

// the band's grip names (firmware wheel.c) -> Brunel gestures
const GRIP_GESTURE = { open: 'open', palm: 'open', fist: 'power_grip', pinch: 'pinch', tripod: 'tripod', point: 'point', close: 'close' };
const FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky'];
const PREVIEW_SPEED = 80;
const KEEPALIVE_MS = 250;
const RETRY_MS = 100;
const clamp01 = v => Math.max(0, Math.min(1, Number(v) || 0));

export function createRelay(hand) {
  const st = { last: null, lastKey: '', applied: 0, grip: 'fist', pending: null, pendingAt: 0, errors: 0, lastError: '', frameAt: 0, clawAt: 0, clawErr: '' };

  const target = () => devices.relay || 'virtual';
  const toVirtual = () => target() !== 'claw';
  const toClaw = () => target() === 'claw' || target() === 'both';

  function applyVirtual(h) {
    const a = h.a || {};
    switch (h.cmd) {
      case 'open': hand.executeGesture('open', hand.speed); break;
      case 'close': hand.executeGesture(GRIP_GESTURE[st.grip] || 'power_grip', Math.max(1, Math.round(20 + 80 * clamp01(a.force ?? 0.5)))); break;   // harder squeeze = faster close
      case 'grip': {
        const g = GRIP_GESTURE[a.name];
        if (!g) throw new Error(`unknown grip '${a.name}'`);
        if (!a.preview) st.grip = a.name;                              // a confirmed grip is what the next close closes into
        hand.executeGesture(g, PREVIEW_SPEED);
        break;
      }
      case 'stop': {                                                    // freeze where it is
        const pos = {};
        for (const [j, s] of Object.entries(hand.snapshot().joints)) if (FINGERS.includes(j)) pos[j] = { position: Math.round(s.position), speed: 100 };
        hand.moveFingers(pos);
        break;
      }
      case 'estop': hand.estop(); break;                               // a no-op while the simulator's interlocks are off; logged either way
      case 'keepalive': hand.keepalive(); break;
      default: throw new Error(`unknown command '${h.cmd}'`);
    }
  }

  function tryVirtual(h) {
    try { applyVirtual(h); st.pending = null; st.applied++; return true; }
    catch (e) {
      if (e.code === 'MOTION_IN_PROGRESS') { st.pending = h; st.pendingAt = Date.now(); }
      else { st.pending = null; st.errors++; st.lastError = e.message; }
      return false;
    }
  }

  async function forwardClaw(h) {
    try { await call('hand', 'POST', `/${h.cmd}`, h.a || {}); st.clawAt = Date.now(); st.clawErr = ''; }
    catch (e) { st.clawErr = e.message; }
  }

  function dispatch(h) {
    st.last = h;
    if (toVirtual()) tryVirtual(h);
    if (toClaw() && h.cmd !== 'keepalive') forwardClaw(h);
  }

  // one frame from the band
  function onFrame(f) {
    st.frameAt = f.rx || Date.now();
    if (f.estop) return estop('frame');
    const h = f.h;
    if (!h || typeof h !== 'object' || !h.cmd) return;
    const key = JSON.stringify(h);
    if (key !== st.lastKey) { st.lastKey = key; dispatch(h); }
    else if (st.pending && Date.now() - st.pendingAt >= RETRY_MS) { st.pendingAt = Date.now(); tryVirtual(st.pending); }
  }

  // the band's ESTOP, from a frame or from its HTTP post
  function estop(source) {
    st.lastKey = ''; st.pending = null; st.last = { cmd: 'estop', a: { source } };
    try { hand.estop(); } catch (e) { st.lastError = e.message; }
    if (toClaw()) forwardClaw({ cmd: 'estop', a: {} });
  }

  // in HAND-FACTUM the band does not keep the hand alive (firmware modes.c); Factum does, while frames are fresh
  setInterval(() => { if (toClaw() && Date.now() - st.frameAt < 1000) forwardClaw({ cmd: 'keepalive', a: { t: Date.now() } }); }, KEEPALIVE_MS).unref?.();

  function view() {
    const s = hand.snapshot();
    return {
      virtual: true, target: target(), grip: st.grip, last: st.last, applied: st.applied, pending: !!st.pending,
      errors: st.errors, lastError: st.lastError, motion: s.motion, estop: s.estop,
      joints: Object.fromEntries(Object.entries(s.joints).map(([j, v]) => [j, Math.round(v.position)])),
      claw: { at: st.clawAt, err: st.clawErr },
    };
  }

  return { onFrame, estop, view };
}
