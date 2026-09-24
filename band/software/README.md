# Band software

C firmware on the Pico SDK 2.2.0 (`firmware/`) plus MicroPython bench tools (`bench/`). The claw's firmware lives
in `claw/software/firmware` and speaks the same protocols. Pins: [../PINOUT.md](../PINOUT.md) (single source of truth). Wiring page: https://claude.ai/artifact/D63qQQRTtqdpi1PEdaQg2D

| dir | target | what |
|---|---|---|
| `firmware/` | Pico 2 W | EMG band: HAND-FACTUM / HAND-DIRECT / MOUSE / HAND-WIRED, config server, BLE HID mouse |
| `../../claw/software/firmware/` | Pico W | claw: hand API on :80, Feetech STS3215 bus, keepalive watchdog, cord |
| `bench/` | MicroPython | `band_bench.py` proves every wire; `listener.py` shows UDP frames on the laptop |

## Build (Windows, Git Bash)
Toolchain lives in `~/.pico-sdk/` (SDK 2.2.0 + submodules, ARM GCC 14.2, prebuilt pioasm/picotool); cmake and
ninja come from the repo's `.venv`. Nothing else to install.
```
sh band/software/firmware/build.sh     # -> band/software/firmware/build/emg_band.uf2
sh claw/software/firmware/build.sh     # -> claw/software/firmware/build/robokyle_hand.uf2
```
Hold BOOTSEL, plug the Pico in, copy the .uf2 onto the RPI-RP2 drive. Serial console on the USB CDC port at
any baud (`putty`, `screen`, or the MicroPico terminal).

## First-time setup
Edit the defaults in `band/software/firmware/src/config.c` and `claw/software/firmware/src/hcfg.c` (Wi-Fi profiles, Factum IP, hand IP, shared key)
before the first flash. After that, change everything from Factum: `POST /config` with header
`X-Factum-Key: <key>` and a partial JSON body (a `wifi` list replaces the whole list; passwords never leave the
devices in `GET /config`). Change the key from the default on first setup.

## Band behaviour
- Boot -> last mode. Button: tap = (reserved), double = next BT slot (MOUSE), 1 s = next mode, 2 s = ESTOP
  (hand modes), 3 s = pair (MOUSE). Two co-contractions within 1 s also switch HAND <-> MOUSE.
- HAND-FACTUM: joins Wi-Fi, classifies on-board, POSTs to the hand, streams UDP frames to Factum:5005.
- HAND-DIRECT: hosts the `RoboKyle` hotspot at 192.168.4.1, the hand joins it. No server needed.
- MOUSE: BLE HID mouse from gyro rates, 4 bonded host slots (blue / cyan / magenta / white), directed advertising
  to the bonded host, undirected while pairing. Flexor burst = left click, hold = drag; extensor burst = right
  click, hold + tilt = scroll; light flexor hold = clutch.
- HAND-WIRED: entered automatically when the hand answers hellos on the cord; radios off; leaves on unplug.
- Grip wheel: co-contraction 150 ms (hand empty) opens it; roll/pitch relative to entry point at 6 sectors
  (open, fist, pinch, tripod, point, palm); the hand previews at low torque; close by returning to centre, 1 s
  still, or 3 s total. Haptics: 1 short = change, 1 long = set, 2 short = cancel/mode, 2 s = ESTOP.
- Config API (port 80): `GET /status` open; `GET/POST /config`, `POST /calibrate {"phase":"rest|close|open|apply"}`
  (10 s captures; apply sets thresholds at 40 % / 25 % of the range), `POST /buzz {"ms":100}`,
  `POST /mode {"mode":0..2}` need the key.

## Hand behaviour
`POST /open`, `/close {"force":0..1}`, `/grip {"name":..,"preview":bool}`, `/stop`, `/estop`, `/keepalive`;
`GET /status`; `GET/POST /config` (key). Any command counts as a keepalive; 500 ms without one while closing ->
stop, then open. ESTOP opens at full torque and latches until power-cycle. Tap the local button = open; hold 2 s
= local ESTOP. Cord: the same commands as `{"cmd":"close","a":{"force":0.4}}` lines; `hello` is answered with
`{"hand":true,"s":{...status...}}`.

Servo positions (`pos_open`, `pos_closed`) and torque limits are in `hcfg` and must be set on the bench with the
claw assembled: move it by hand with torque off, read `GET /status` `pos` at each end.

## Status of the code
Compiles clean against SDK 2.2.0 with no warnings in our sources. Not yet run on hardware. The pieces most likely
to need a first-run fix: the BNO08x SHTP read sequence in `firmware/src/imu.c` (compare against Adafruit's
`Adafruit_BNO08x` HAL if it stalls), directed advertising parameters in `ble_mouse.c` (an iPhone may want
undirected + whitelist instead), and the Feetech register map in `claw/software/firmware/src/feetech.c` (verify against the STS3215
memory table).
