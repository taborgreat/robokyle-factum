# Robo Kyle EMG band + claw — handoff for Claude Code

You are continuing a hardware project with Tabor. Read this file first, then band/BUILD.txt and claw/README.txt.
The CAD so far was done in OpenSCAD by reasoning + renders, without real part solids or interference checks, and it
has produced fit errors. The job now is to rebuild the enclosures in **agentcad (build123d)** with every real part
modeled as a named solid, pockets derived from those solids + clearance, and interference/spec checks on every version.
Do not re-export STLs from the .scad files as a first step; use them only as the layout reference.

## Who / what
- Tabor: solo builder, Rust/backend, Oregon. Building for his friend Kyle (left arm ends at the wrist; other arm very short,
  so everything is one-handed, and the box's switch must face his chest). Site: robokyle.org. Server: Factum (his own).
- Collaborator Chad builds the Brunel Hand side (Arduino UNO R4 WiFi HTTP server). Chad's timeline is uncertain, so Tabor is
  also building a DIY claw (claw/) that speaks the same HTTP endpoints.

## System (decided, do not re-litigate)
- Band = sleeve + upper-arm cuff box + forearm elastic ring with 3 pucks. Band is the hand's ONLY commander (classifies
  on-board, POSTs open/close/stop/estop + 250 ms keepalive). Factum is a listener only (UDP frames for logging/calibration/arcade).
- Four modes: HAND-FACTUM (home Wi-Fi), HAND-DIRECT (band hosts a Wi-Fi AP, hand joins), MOUSE (BLE HID mouse, up to 4 hosts:
  PS5, MacBook, iPhone; Apple TV skipped), and HAND-WIRED: an optional 3-wire UART cord band<->hand (JST both ends, GP0/GP1,
  115200, JSON lines). The cord is detected by hellos every second; when the hand answers, the band drops ALL radios and
  leaves mouse mode (the two muscles can't be mouse and grip at once), button/muscle mode changes are ignored, and unplugging
  returns to the last wireless mode. Keepalive/500 ms open rule applies on the wire too. Purpose: multi-day battery.
  Mouse from gyro rates (dead zone + accel curve), arm relaxed at the side.
- Grip wheel: co-contraction opens it only when the hand is empty; arm orientation points at fixed clock positions; the hand
  previews each grip live at low force; closing the wheel keeps what it shows. Haptics: 1 short = change, 1 long = set,
  2 short = cancel/mode, 2 s buzz = ESTOP. Proportional force from flexor effort.
- Firmware: C with Pico SDK + BTstack (CircuitPython can't do multi-host directed advertising). Rust/embassy+trouble is the alt.
- One button on the box: tap = recenter; double-tap = next BT slot (MOUSE); 1 s = mode; 3 s (MOUSE) = pairing; 2 s (HAND) = ESTOP.
- Charging: Qi receiver coil in the lid (ferrite toward the Pico), 5 V -> 1N5817 -> Pico VBUS. Pico micro USB also charges
  (SunFounder module hangs on VBUS/VSYS/GND). Kill switch is on the VSYS lead: off = band dead, battery still charges.
- Stand: wall/table panel with six open-top hooks catching loops on the sleeve; hanging the sleeve drops the box into a cradle
  over the Qi pad. One-handed on/off + charging in one motion. Not designed yet.
- Sweat/rain: conformal coat boards, TPU plugs for USB/switch, epoxy the LED, grommet the cable exit, silicone bead in the lid lip.
  FINAL BOX HAS NO OPEN HOLES — every opening is filled by a part or a plug.

## Band electronics (all owned)
- Raspberry Pi Pico W (original, not 2 W). Pins: GP26 sensor1 (flexor), GP27 sensor2 (extensor), GP28 battery divider
  (2x100k), GP4/GP5 I2C -> GY-BNO08X (PS0,PS1,AD0 -> GND; RST,BOOT -> 3V3; use Game Rotation Vector only, 50 Hz),
  GP14 button (pull-up), GP15 -> 1k -> 2N2222 -> coin motor (1N4148 across motor), GP16/17/18 -> 220R -> 3 mm RGB LED.
- 2x DFRobot SEN0240 (dry 3-dot electrode board + signal board + Gravity 3-pin cable). Output ~1.5 V-centered; Pico samples
  ~1 kHz, mean |v-1.5| per 20 ms = effort. NOT YET ARRIVED — electrode board dims are a guess (38x22x4).
- EEMB 803048 LiPo 1200 mAh 50 x 30.5 x 8.3, JST-PH 2.0 (check red/black polarity vs the module!).
- SunFounder Kepler-kit Li-po charger module: 19 x 6.5 x 7 mm, header pins hang ~8 mm below; charges through the Pico's USB.
- Slide switch, tactile button, 3 mm RGB LED, 10 mm coin motors, JST-PH kit (housings, PCB sockets, loose pins) + SN-01BM crimper,
  ELEGOO perfboard (Pico soldered flat on a 25x60 strip; JST sockets at strip ends), M2 screws, M2x4 heat-set inserts, Kapton,
  foam roll, 1/4" braided sleeving, Zerone Qi receiver (coil ~40x30 + small board + ferrite "magnetic spacer"), 1N5817 pack,
  Yootech Qi pad, CAMBIVO elbow compression sleeve (2-pack), 1.5" knit elastic (forearm ring, no fastener).

## Band CAD state (band/band.scad = v4 cuff)
- Cuff box wraps the arm (R44 upper arm, guessed), 80 x 68 footprint, ~19.4 mm radial thickness incl 2.2 mm sewn plate.
  Battery bay tilted tangent at y=-14.5 (posterior/humerus side); Pico strip tangent at y=+14.5 (anterior). Charger at the -X
  (USB) end. Switch slot in the +Y (chest-facing, `front=1`) wall near +X (elbow) end. Cable exit +X wall. Button + LED on lid
  (chest edge / triceps edge). Qi board frame + motor cradle on lid underside. Plate: 4 vertical bosses w/ M2 inserts, eyelets.
- Pucks: electrode puck (window for the 3 dots, shims behind), IMU puck (slotted bosses 16-22 mm, IMU 24x14.5), both with slots
  for the elastic ring. IMU puck doubles as the cable hub (3 JST sockets). Trunk: 6 wires in sleeving, JST both ends.
- KNOWN PROBLEMS reported from the first print: pockets were part+0.3 mm (too tight for FDM; now clr=1.2 everywhere but unverified),
  the charger pocket had no room for the battery plug, the USB slot is a big hole (should be plug-sized + TPU plug),
  and features placed by arm-angle drifted outward at larger radii (fixed by vertical screws + `on_out`, but verify).
  A lid that "overhung by centimeters" was almost certainly a stale STL from an earlier folder; the current meshes match.

## Claw CAD state (claw/claw.scad, v1, gear version)
- Two fin-ray TPU fingers on module-2 printed gears, STS3215 7.4 V 1/345 standing at the front, Pico 2 W + driver board + 2S
  1000 mAh pack + 2S BMS + USB-C boost charger (set 2S/1A) + buck 5 V + kill switch in the rear bay, cuff stub w/ 4x M4 at rear.
- Tabor may prefer direct drive (one fixed finger, one on the servo horn, no gears). Conductive fingertip wire channels exist.
- Nothing printed yet. Servo/horn/pack/driver dims are guesses; measure before the body.

## Firmware (firmware/ next to this file, C, untested skeletons)
- band/: Pico W SDK + lwIP + BTstack. Modules: config (flash), io, emg, imu (BNO08x GRV+gyro), net (STA/AP/UDP/HTTP POST),
  factum (frame contract), hand (API; routes over the cord when present), wheel, ble_mouse (HOGP, 4 slots, directed adv),
  wire (cord detection/transport), modes (per-mode logic, cord override), main. API names marked VERIFY need checking.
- hand/: Pico 2 W. httpd (raw lwIP HTTP: /open /close /grip /stop /estop /keepalive /status), feetech (STS3215 protocol),
  gripper (force->torque limit, keepalive watchdog opens, estop latches), wire (UART cord, same commands as JSON lines), main.
- Both need the box's cable exit to carry one extra 3-pin JST for the cord (add to the CAD parts library).
- Config API on both (port 80): GET /status (open), GET/POST /config (partial JSON merge into flash), band also
  POST /calibrate, /buzz, /mode. Only Factum may write: requests must carry header `X-Factum-Key: <shared secret>` stored
  in each device's flash config (change from the default on first setup). Up to 4 Wi-Fi profiles per device, tried in
  order (ship with Tabor's and Kyle's networks in the defaults). Kyle uses Factum's web UI from anywhere; Factum reaches the
  devices on the LAN. Factum is a listener for frames and the only writer of settings; it never sits in the hand command path.

## FIRST SESSION PLAN (agentcad)
1. `python3.12 -m venv .venv && pip install agentcad[mcp] && agentcad init --name emg-band`; add the MCP entry.
2. Build `parts.py`: named solids + keep-outs for every part above, from Tabor's calipers (ask for each number; do not guess):
   Pico W + header base + micro USB plug inserted; EEMB cell + lead loop; charger module + battery plug seated; slide switch +
   nub travel; button + legs; 3 mm LED; coin motor; JST-PH 2/3/4/6 housings + 10 mm wire bend; Qi board + coil + ferrite;
   GY-BNO08X; SEN0240 electrode + signal boards (when they arrive).
3. Build the cuff box by subtracting (parts + clr) from the cuff solid; plate; lid with lip. Keep the decided layout.
4. `spec.json` with every pocket/hole; run `check-spec` each version; add an interference script (intersect each part with
   the box; any volume > 0 is a fail). Export STL only when green; print measured sizes with each export.
5. Then the pucks, then the claw (direct-drive variant first), then the stand.

## Rules Tabor set
- Ask before "minor adjustments" that ripple; batch fixes; one folder of outputs, overwrite in place, never leave stale copies.
- Report mesh bounding sizes with every export so he can verify what's loaded in Bambu Studio.
- Print fast prototypes for fit; he checks physical parts and sends photos.
