import React from 'react';

const JOINTS = ['thumb', 'index', 'middle', 'ring', 'pinky', 'thumb_rotator'];

// The virtual Brunel hand lives inside this server at /brunel/: its viewer in the frame below, its Open Bionics API
// underneath it. In HAND-FACTUM the band's frames carry the hand command, and Factum's relay applies it here.
export default function Brunel({ state }) {
  const v = state.status?.virtual;
  const where = v?.target === 'claw' ? 'the claw only' : v?.target === 'both' ? 'the virtual hand and the claw' : 'the virtual hand';
  return (
    <>
      <div className="grid">
        <div className="panel stat"><span className="k">relay</span><span className="v">{v?.target || '–'}</span><span className="s">the band's hand command goes to {where} · change it under Devices</span></div>
        <div className="panel stat"><span className="k">grip</span><span className="v">{v?.grip || '–'}</span><span className="s">{v?.last ? `last: ${v.last.cmd} ${JSON.stringify(v.last.a || {})}` : 'no command from the band yet'}</span></div>
        <div className="panel stat"><span className="k">hand</span><span className="v">{v ? v.motion : '–'}</span><span className="s">{v ? `${v.applied} applied · ${v.pending ? 'one waiting for the motion to finish' : 'idle'}${v.errors ? ` · ${v.errors} refused: ${v.lastError}` : ''}` : 'relay not running'}</span></div>
        <div className="panel stat"><span className="k">joints</span><span className="v mono" style={{ fontSize: '1.1rem' }}>{v ? JOINTS.map(j => v.joints?.[j] ?? 0).join(' / ') : '–'}</span><span className="s">thumb / index / middle / ring / pinky / thumb rot. · % closed</span></div>
      </div>
      <div className="panel wide">
        <div className="actions" style={{ marginBottom: 8 }}>
          <h2 style={{ margin: 0 }}>Virtual Brunel hand</h2>
          <a className="btn secondary" href="/brunel/" target="_blank" rel="noreferrer">Open on its own</a>
        </div>
        <p className="msg">The band's grip-wheel previews and its open and close arrive here as the same Open Bionics API calls the real Brunel takes (POST /brunel/gesture/execute and friends). The EMG panel inside the viewer is its own keyboard simulator; with the band streaming, watch the hand, not that panel.</p>
        <iframe title="Virtual Brunel hand" src="/brunel/" className="viewer" />
      </div>
    </>
  );
}
