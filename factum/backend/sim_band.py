"""Fake band for developing Factum without hardware: streams plausible frames at 50 Hz to UDP 5005 and answers the
band's HTTP API on :8081 (point Devices -> band IP at 127.0.0.1 and port at 8081 to test settings pages).

    python backend/sim_band.py
"""
import json, math, socket, threading, time, random
from http.server import BaseHTTPRequestHandler, HTTPServer

CFG = {"band_id": "band1", "factum_ip": "127.0.0.1", "factum_port": 5005, "hand_ip": "192.168.1.11", "hand_port": 80,
       "ap_ssid": "RoboKyle", "flex_on": 0.3, "flex_off": 0.18, "ext_on": 0.3, "ext_off": 0.18, "flex_max": 0.9,
       "force_limit": 0.6, "mouse_gain": 0.08, "mouse_deadzone": 3.0, "mouse_accel": 1.4, "last_mode": 0, "bt_slot": 0,
       "wifi": [{"ssid": "TABOR_WIFI"}, {"ssid": "KYLE_WIFI"}]}
KEY = "change-me-on-first-setup"
state = {"t0": time.time(), "seq": 0, "mode": 0}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj): b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _auth(self): return self.headers.get("X-Factum-Key") == KEY
    def do_GET(self):
        if self.path == "/status": return self._send(200, {"id": "band1", "mode": state["mode"], "wired": False, "battery": 3.91, "pct": 72, "uptime": int(time.time() - state["t0"]), "ip": "127.0.0.1", "rssi": -58, "c": [0.02, 0.02], "intent": 0, "imu": True, "o": [10, -3, 1]})
        if not self._auth(): return self._send(401, {"error": "X-Factum-Key required"})
        if self.path == "/config": return self._send(200, CFG)
        self._send(404, {"error": "no such endpoint"})
    def do_POST(self):
        if not self._auth(): return self._send(401, {"error": "X-Factum-Key required"})
        n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/config": CFG.update({k: v for k, v in body.items() if k not in ("wifi", "factum_key", "ap_pass")}); return self._send(200, {"saved": True})
        if self.path == "/mode": state["mode"] = int(body.get("mode", 0)); return self._send(200, {"ok": True})
        if self.path == "/calibrate": return self._send(200, {"phase": 0, "have": 7, "rest": [0.02, 0.02], "close": 0.6, "open": 0.5, "k": 500})
        if self.path == "/buzz": return self._send(200, {"ok": True})
        self._send(404, {"error": "no such endpoint"})
    def log_message(self, *a): pass

def stream():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        t = time.time() - state["t0"]; state["seq"] += 1
        fist = 0.55 if int(t) % 6 in (2, 3) else 0.0; spread = 0.45 if int(t) % 9 == 6 else 0.0
        f = {"id": "band1", "seq": state["seq"], "t": int(t * 1000), "c": [round(0.02 + fist + random.gauss(0, .01), 3), round(0.02 + spread + random.gauss(0, .01), 3)],
             "b": 3.91, "o": [round(20 * math.sin(t / 3), 1), round(10 * math.cos(t / 5), 1), round(5 * math.sin(t / 7), 1)], "i": 1 if fist else 2 if spread else 0}
        s.sendto(json.dumps(f).encode(), ("127.0.0.1", 5005)); time.sleep(0.02)

threading.Thread(target=stream, daemon=True).start()
print("sim band: frames -> udp/5005, api on http://127.0.0.1:8081")
HTTPServer(("127.0.0.1", 8081), H).serve_forever()
