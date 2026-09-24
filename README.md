# Robo Kyle

Myoelectric band + claw for Kyle, with Factum as the server in the middle. The band is the hand's only commander
(classifies on-board, POSTs open/close/stop/estop + keepalive); Factum only listens and is the only writer of settings.
Modes: HAND-FACTUM, HAND-DIRECT (band hotspot), MOUSE (BLE HID), HAND-WIRED (3-wire cord, automatic).

| folder | what |
|---|---|
| `band/` | the EMG band: `hardware/` (CAD, prints, bench guide), `software/` (Pico 2 W firmware, bench scripts), `PINOUT.md` |
| `claw/` | the DIY hand: `software/` (Pico W firmware); `hardware/` to be rebuilt |
| `factum/` | Node backend + React frontend: listens to the band, edits both devices' settings |

Tooling: `.venv` (agentcad/build123d, cmake, ninja), `~/.pico-sdk` (SDK 2.2.0 + ARM GCC), Node 22. Generated CAD
versions land in `build/` (ignored); exported STLs in `band/hardware/print/`.
