# Factum

Kyle's server: it listens to the band, drives the hand the band is wearing for in HAND-FACTUM, shows what it sees,
and is the only thing allowed to change device settings. Node backend + React frontend + the virtual Brunel hand,
one deployable (copy this folder to the server PC). The band reaches it at `api.factum.org`: UDP frames on 5005,
its ESTOP post on `/band/estop`.

```
cd factum/backend && npm install && npm start          # http://localhost:8080, UDP 5005, virtual hand at /brunel/
cd factum/frontend && npm install && npm run build      # backend serves frontend/dist
# dev: npm run dev in frontend (Vite on :5173, proxies /api, /ws, /brunel and /band to :8080)
python backend/sim_band.py                              # fake band for working without hardware (frames carry `h`)
```

Env: `PORT` (8080), `UDP_PORT` (5005), `DATA_DIR` (backend/data). Data: `devices.json` (IPs, shared key, relay
target; the key never goes to the browser), `frames-YYYY-MM-DD.jsonl` (every frame, from the first session),
`brunel-eeprom.json` (the virtual hand's saved gestures).

Pages: **Live** (rate, mode, battery, intent, orientation, hand, the band's hand command and where it went, 20 s
effort chart with the band's thresholds, ESTOP log) · **Band** (thresholds, mouse, feedback, Factum address, hotspot,
Wi-Fi list, calibration wizard, buzz, mode, key) · **Brunel** (the virtual Brunel hand, live, inside the page; its
Open Bionics API is `/brunel/*`) · **Claw** (Kyle's claw: coming soon; its settings go live when it answers) ·
**Devices** (IPs, key, which hand the relay drives, log files).

## HAND-FACTUM: how the band drives a hand through here

The band never addresses a hand over Wi-Fi. Every frame carries `h`, the command it would have sent
(`{"cmd":"close","a":{"force":0.6}}`, `grip {name, preview}`, `open`, `stop`, `estop`, `keepalive`). `backend/src/relay.js`
applies it when it changes: to the virtual Brunel as Open Bionics API calls (grip names map to gestures, a harder
squeeze closes faster), and, when Devices says so, to the claw over the band's own protocol (`POST /open`, `/close`,
`/grip` on the claw's IP), with Factum feeding the claw's keepalive while frames flow. The band's ESTOP arrives twice,
as UDP frames and as `POST /band/estop`; both stop the hand and land in the ESTOP log.

## The virtual Brunel hand (`brunel/`)

Imported with its history from `taborgreat/robokyle` (`virtualBrunel/`). A simulator of the Open Bionics Brunel
Hand's HTTP API (`brunel/Brunel Hand API Specification.pdf`) driving a three.js hand, plus a keyboard EMG simulator
of its own. Mounted at `/brunel/` by the backend (`createBrunelHand` in `brunel/index.js`); three.js is served from
the backend's `node_modules`. It also still runs on its own: `cd brunel && npm install && npm start`. The band's
`band.md` in there is the early spec it was written against; `band/` in this repo is the truth now.

Next: a virtual claw on the Claw page driven by the same relay, and the arcade adapter.
