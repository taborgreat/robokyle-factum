# Factum

Kyle's server: listens to the band, shows what it sees, and is the only thing allowed to change device settings.
Node backend + React frontend, its own deployable (copy this folder to the server PC).

```
cd factum/backend && npm install && npm start          # http://localhost:8080, UDP 5005
cd factum/frontend && npm install && npm run build      # backend serves frontend/dist
# dev: npm run dev in frontend (Vite on :5173, proxies /api and /ws to :8080)
python backend/sim_band.py                              # fake band for working without hardware
```

Env: `PORT` (8080), `UDP_PORT` (5005), `DATA_DIR` (backend/data). Data: `devices.json` (IPs + shared key —
never sent to the browser) and `frames-YYYY-MM-DD.jsonl` (every frame, from the first session).

Pages: **Live** (rate, mode, battery, intent, orientation, hand state, 20 s effort chart with the band's
thresholds, ESTOP log) · **Band** (thresholds, mouse, network, Wi-Fi list, calibration wizard, buzz, mode, key) ·
**Hand** (servo end positions, torques, Wi-Fi) · **Devices** (IPs, key, log files).

Not here on purpose: the HAND-FACTUM forwarding path (band → Factum → hand). The band commands the hand directly;
Factum only listens. The arcade adapter and the light-mode editor are next.
