"""UDP frame listener for the bench test and the real band. Run on the laptop:

    python firmware/bench/listener.py            # listens on 0.0.0.0:5005

Prints one line per frame with the gap since the previous frame and the sequence jump, so dropouts show up.
Build-order level 1 passes when this shows 50 frames/s for 10 minutes with no seq gaps.
"""
import json
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", 5005))
print("listening on udp/5005 - Ctrl-C to stop")
last_seq, last_t, n, t_start = None, None, 0, time.time()
try:
    while True:
        data, addr = s.recvfrom(2048)
        now = time.time()
        try:
            f = json.loads(data)
        except ValueError:
            print("bad json:", data[:80]); continue
        seq = f.get("seq")
        gap = "" if last_seq is None or seq == last_seq + 1 else f"  SEQ GAP {seq - last_seq - 1}"
        dt = 0 if last_t is None else (now - last_t) * 1000
        n += 1
        rate = n / max(now - t_start, 1e-6)
        print(f"{addr[0]} seq={seq} dt={dt:5.1f}ms rate={rate:5.1f}/s c={f.get('c')} b={f.get('b')} o={f.get('o')}"
              f"{'  ESTOP' if f.get('estop') else ''}{gap}")
        last_seq, last_t = seq, now
except KeyboardInterrupt:
    print(f"\n{n} frames in {time.time() - t_start:.0f} s")
