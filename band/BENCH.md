# Bench guide — jumper-wire everything, prove it, then solder

Read with [PINOUT.md](PINOUT.md) (pins) and the wiring page (https://claude.ai/artifact/D63qQQRTtqdpi1PEdaQg2D).
Rule of the bench: **one new thing at a time, and a check after each.** Never add a part to a circuit you haven't
proved yet. Battery out of the circuit until stage 2 says so.

## 0. Parts on the bench

| part                      | job                                            | notes                                                          |
| ------------------------- | ---------------------------------------------- | -------------------------------------------------------------- |
| Pico 2 W (on headers)     | brain, Wi-Fi, BLE                              | goes in the band; bare Pico W goes to the hand later           |
| breadboard + jumpers      | the whole box, temporarily                     | keep power on one end, signals on the other                    |
| SunFounder charger module | charges the cell, protects it, powers the Pico | VI in, VO out, GND, JST socket                                 |
| EEMB 1200 mAh cell        | power                                          | **check polarity at the JST: red must land on the socket's +** |
| slide switch              | kill switch                                    | middle pin + one outer pin                                     |
| 1N5817 × 2                | one-way valves                                 | stripe = cathode = the side current flows OUT of               |
| 1N4007 (SunFounder kit; 1N4148 also fine) | motor kick-back | stripe toward 3V3 |
| S8050 NPN (SunFounder kit; 2N2222 also fine) | motor switch | flat face toward you, legs down: **E B C** on both; verify on the datasheet for your brand |
| 1 kΩ, 470 Ω, 100 kΩ × 2 | base resistor, LED resistor, divider | colour bands: brown-black-red, yellow-violet-brown, brown-black-yellow |
| coin motor, 5 mm green LED, 12 mm yellow button, WS2812 strip (cut 3 pixels) | UI | LED soldered into the strip (shows through the lid); bar lies in the middle-wall pocket; button + motor in the forearm module (trunk A) |
| GY-BNO08X | orientation | I²C address 0x4B with AD0 low; **lives in the forearm module, not the box** |
| SEN0240 × 2 (plate + signal board + 3.5 mm cable) | EMG | boards in the forearm module, plates on their loop band; the Gravity cables are not used |
| JST-PH kit: 6-pin sockets × 2, 4-pin sockets × 2, 3-pin socket × 1, housings + crimp pins | every connector | box: PH6 + PH4 + PH3 in the walls; module: PH6 + PH4 stacked |
| 1.5" elastic strap, ≤ 22 mm elastic (loop band), M2 × 4/6/8/12 screws, M2 heat-set inserts | mounting | see PUCKS.md |
| Qi receiver + coil + ferrite | wireless charging | last thing you add |
| Kapton tape (amber) | insulation, heat-proof | around the cell's edges, over solder stubs, holds ferrite to coil and coil to lid |
| (optional, later) foil shield | conductive | only if the EMG trace is noisy: kitchen foil around the twisted EMG1/EMG2/GND trio with a bare wire under it to GND at the box end; **never near the Qi coil** |
| multimeter | your eyes | DC volts; also continuity (beep) for checking joints |

## 1. Power, without the Pico

Wire only: charger module, switch, diode 1, and the meter.

1. Cell → charger JST. Meter across the **JST + pin and GND**: cell voltage, 3.6–4.2 V. If it reads negative, STOP — polarity is reversed; re-pin the plug.
2. Meter across **VO and GND**: either ~5.0 V (boost version) or the cell voltage (pass-through version). Write down which — it decides the LED resistor (470 Ω for 3V3 feed either way, but good to know).
3. VO → switch middle. Switch outer → diode 1 plain end. Meter from **diode 1 stripe end to GND**: switch on → VO minus ~0.3 V; switch off → 0 V. That's your kill switch working.

**Pass:** cell voltage correct polarity, VO present, switch kills the diode output.

## 2. Pico alone, MicroPython, blink

1. Hold BOOTSEL, plug the Pico into the PC, drop the **MicroPython Pico W / Pico 2 W .uf2** on the RPI-RP2 drive.
2. Open the MicroPico terminal (VS Code) or any serial terminal. You should get `>>>`.
3. Type `from machine import Pin; Pin("LED", Pin.OUT).toggle()` — the onboard LED toggles. The Pico is alive.

## 3. Pico on battery power

1. Diode 1 stripe → Pico **pin 39 (VSYS)**. Charger GND → Pico **pin 38**. Nothing else.
2. Unplug USB, switch on: onboard LED behaviour as before when you run the toggle from a saved `main.py` (write a two-line blink `main.py` first, over USB).
3. Plug USB back in **with the switch on**: nothing bad happens (the diode is doing its job). Charger LED on: Pico pin 40 → **VI** is now the charge path.

**Pass:** blinks on battery alone; USB + battery together is fine; switch off kills it.

## 4. Peripherals, one at a time, with `bench/band_bench.py`

Copy `band/software/bench/band_bench.py` to the Pico as `main.py` (or run it from MicroPico). It prints a status line
every 150 ms and runs a self-test on the button. Add parts in this order and watch the line change:

| add                 | wiring                                                                                     | what the bench script shows                                                        |
| ------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| **button**          | GP14 ↔ one leg, GND ↔ diagonal leg                                                         | `BTN 1` while pressed; tap = buzz attempt + pixel chase (nothing yet, that's fine) |
| **WS2812 (3 px)**   | +5V pad → 3V3 (pin 36), GND → GND, DIN → GP16                                              | self-test colours R G B W at boot; then pixels 0/1 meter the EMG                   |
| **motor circuit**   | GP15 → 1k → base; E → GND; 3V3 → motor → C; 1N4007 across the motor, stripe to 3V3         | tap the button: a 60 ms buzz. If it hums weakly, the transistor legs are swapped   |
| **green LED**       | 3V3 → 470 Ω → long leg; short leg → GND                                                    | on whenever the Pico is on (no code involved)                                      |
| **battery divider** | JST + → 100k → GP28 → 100k → GND                                                           | `BAT 3.9x V` matches the meter on the cell within 0.05 V                           |
| **BNO08x**          | 3V3→VIN, GND→GND, GP4→SDA, GP5→SCL, GP6→INT, GP7→RST, PS0/PS1/AD0→GND                      | `IMU ok 0x4b`                                                                      |
| **SEN0240 #1**      | signal board: + → 3V3, − → GND, S → GP26; 3.5 mm cable to the plate; plate on your forearm | `flex=` sits ~0.02 at rest, rises to 0.2–0.5 when you make a fist                  |
| **SEN0240 #2**      | same on GP27                                                                               | `ext=` rises when you spread your fingers hard                                     |

Tips: hold the plate against the inside of your forearm a third of the way down from the elbow, bars along the arm,
firmly. Damp skin helps. If both channels sit at 0 or at 1.5 flat, the plate isn't making contact. This is the
bench: on the breadboard the IMU and EMG boards sit next to the Pico. In the build they live in the forearm module
and reach the box through the trunk (stage 8).

**Pass:** every column of the status line responds to the real world.

## 5. Wi-Fi frames to the laptop

1. In `band_bench.py` set `WIFI_SSID`, `WIFI_PASS`, and `UDP_HOST` to your laptop's LAN IP.
2. On the laptop: `python band/software/bench/listener.py`.
3. Expect ~50 frames/s, no `SEQ GAP` lines, for 10 minutes. That is build-order level 1 from the spec.
4. Optional: start Factum (`cd factum/backend && npm start`, open http://localhost:8080) — the Live page shows the
   same frames with the chart.

## 6. The real firmware

1. Build: `sh band/software/firmware/build.sh` (defaults to the Pico 2 W).
2. Before flashing, edit `band/software/firmware/src/config.c` defaults: Wi-Fi SSID/password, Factum IP, hand IP, and change
   the shared key. Rebuild.
3. BOOTSEL + copy `build/emg_band.uf2`. Open the serial console (any baud). Expected boot log:
   `config: defaults` → `imu: BNO08x fw x.y.z` → `net: joining <ssid>` → `net: <ssid> ip 192.168.x.x` → `cfgsrv: listening on :80`.
   Light bar: green blink while joining, solid green when joined.
4. From the laptop: `curl http://<band ip>/status` → JSON. Factum's Devices page learns the IP from the first frames.
5. Button: 1 s hold cycles modes (buzz twice each time). Double-tap in MOUSE moves the BT slot. 3 s in MOUSE pairs:
   the band shows up as **RoboKyle Band** in a phone/laptop Bluetooth list; once paired, moving the IMU moves the
   cursor and a fist clicks.
6. Calibration from Factum → Band → Calibrate: rest / close / open / apply. Thresholds save to flash.

**Pass:** status over HTTP, frames in Factum, mode switch on the button, BLE mouse moves a cursor.

## 7. Now solder (only after 6 passes)

Where tall parts may go on the strip (the CAD checks these zones): the rib-side outer row anywhere from 20 mm
before the strip centre to the free rows, and the chest-side outer row except under the switch (8 +- 6 mm from the
strip centre) and under the LED (18 +- 5 mm) - keep those two spots for flat parts. Nothing over 4.5 mm.


Standoffs: the board's four drilled holes are at rows 2 and 21, columns 1 and 10 (±24.13 × ±11.43 from the board
centre) and the box's posts match them - three posts; the USB-end rib-side corner of the board is snipped ~8 mm
because the lid's boss stands there, so that hole is unused, and the USB-end chest-side corner is nipped ~2 mm at
45° to clear the bay's rounded corner. What is on the strip: the Pico, the green LED standing
in rows 21-22, third column in on the chest side (columns 1/10 of those rows are beside the standoff screws), its
470 Ω lying flat beside it toward the centre (clip the LED's legs 1.5 mm under the board like every other part),
the divider pair, the motor driver (1k / S8050 / 1N4007), diode 1, and wires to the
charger corner, the wall sockets and the light bar. Nothing else - the IMU, the EMG boards, the
button and the motor are in the forearm module.

Order on the strip: Pico headers → star ground blob (row 22, outer columns - the lid sockets sit over the middle of
rows 21-22) → 470 Ω + LED wires → 100k pair → 1k / S8050 / 1N4007
→ diode 1 → wires to the charger corner (VI, VO, GND, JST+) → wall sockets (PH6 trunk A in the battery-side end
wall, PH4 trunk B + PH3 cord in the strip-side end wall: 60 mm leads soldered to the socket pins clipped to 2 mm,
sockets dropped into their wall pockets **before the battery goes in** - the PH6's wires run behind the battery
ring) → three 60 mm leads on the light bar's -X pads (GND, +5V, DIN) down to the strip (GND, 3V3, GP16); the bar
lies in the middle wall's pocket, LEDs up, leads through the USB-end notch. The LED is a strip part: solder it
standing 1 mm off the board, long leg toward the 470 Ω; the lid's hole lands over its dome. Nothing is on the lid. Test with the bench script again after the strip is done and before
it goes in the box. Then conformal coat, then box. Box assembly order (fit-checked in the CAD): wall sockets with their leads
→ charger in its cradle, socket toward the middle wall → Kapton, Qi board on top → battery (lip toward the charger,
leads through the ring's notch) → ferrite + coil on the battery → strip onto its four standoffs (M2 thread-forming)
→ light bar into its pocket → lid on, two M2x6 into the inserts. Box to plate:
two M2x6 from inside, down through the small bosses on the battery-side floor into the plate posts' inserts
(the post sits inside the boss; the screw head pulls the boss's web onto the brass), before the strip goes in.

Tape, in order: Kapton over the strip's solder side (leave the standoff holes clear) → Kapton around the cell's four
edges and the tape lip → charger module wrapped once → coil: ferrite on the inner face, Kapton over both, then Kapton
tabs to the lid underside over the battery bay → Kapton over the charger's soldered wires → Qi board flat on it,
parts up, coil/output wires down its rib-side edge (the lid holds it). Trunk: twist
EMG1/EMG2 with a GND wire, then the braided sleeving over everything (foil shield only if the bench shows noise). All tapes are under 0.1 mm; the pockets already allow for it.

## 8. Forearm ring and the cables

Build and wiring for the forearm module and the electrode frames are in [hardware/PUCKS.md](hardware/PUCKS.md).
Cables to crimp (PH housings on both ends, 26-28 AWG silicone):

| cable | ends | length | notes |
|---|---|---|---|
| trunk A | PH6 ↔ PH6 | 25 cm | 3V3, GND, EMG1, EMG2, BTN, MOTOR - twist EMG1/EMG2 together with GND (that is the shielding for v1) |
| trunk B | PH4 ↔ PH4 | 25 cm | SDA, SCL, INT, RST |
| hand cord | PH3 ↔ PH3 | as needed | TX, RX, GND, **crossed** (band TX → hand RX); HAND-WIRED mode |
| plate cables | 3.5 mm ↔ 3.5 mm | the kit's | one per electrode, plate jack → module wrist wall |

At the module the two trunk housings are glued face-to-face into one block (PH6 below, PH4 above, one tall
window); at the box they go into two different walls, so they stay separate there. Glue the module end **after**
a first plug-in so the pair sits square. Braided sleeving over both trunk cables together.

Bench test of the ring: plug the trunk into the box, run the stage-4 bench script; `IMU ok 0x4b` and both EMG
columns must behave exactly as they did on the breadboard. If `IMU` fails, it is INT/RST swapped in trunk B.

## Safety, short version

- LiPo: never short the JST, never charge unattended the first time, never charge while worn. Warm is normal; hot is not.
- Check the JST polarity with the meter before plugging the cell into the module. Suppliers do not agree on red/black.
- Diodes backwards do nothing (fine) or short things (not fine). Stripe = the end current leaves from.
- The Pico's 3V3 pin can give ~300 mA total. Everything we hang on it adds up to ~150 mA. Don't add a servo to it.
