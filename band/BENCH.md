# Bench guide — jumper-wire everything, prove it, then solder

Read with [PINOUT.md](PINOUT.md) (pins) and the wiring page (https://claude.ai/artifact/D63qQQRTtqdpi1PEdaQg2D).
Rule of the bench: **one new thing at a time, and a check after each.** Never add a part to a circuit you haven't
proved yet. Nothing on the Pico until stage 3 says so.

## 0. Parts on the bench

| part                      | job                                            | notes                                                          |
| ------------------------- | ---------------------------------------------- | -------------------------------------------------------------- |
| Pico 2 W (on headers)     | brain, Wi-Fi, BLE                              | goes in the band; bare Pico W goes to the hand later           |
| breadboard + jumpers      | the whole box, temporarily                     | keep power on one end, signals on the other                    |
| AITRIP TP4057 1A Type-C charger board (12.1 × 16.8, 18.35 with the USB-C, 4.2 tall) | charges the cell from the Qi pad, protects it | pads **B+ B−** (cell), **OUT+ OUT−** (to the switch / ground - the protection FET is in OUT−), **IN+ IN−** (5 V in: from the Qi receiver through a 1N5817, and from Pico pin 40 through another 1N5817, the two diodes meeting at IN+). Its own USB-C stays unused inside the box. Charges at 1 A, right at the Qi receiver's limit: swapping its PROG resistor from 1 kΩ (102) to 2 kΩ (202) gives ~500 mA, cooler and kinder to the receiver, optional. |
| EEMB 1200 mAh cell        | power                                          | **check polarity at the JST: red must land on the socket's +** |
| slide switch              | kill switch                                    | middle pin + one outer pin                                     |
| 1N5817 × 3                | one-way valves: cell → VSYS (diode 1), Qi + → charger IN+ (diode 2), Pico VBUS → charger IN+ (diode 3) | stripe = cathode = the side current flows OUT of               |
| 1N4007 (SunFounder kit; 1N4148 also fine) | motor kick-back | stripe toward 3V3 |
| S8050 NPN (SunFounder kit; 2N2222 also fine) | motor switch | flat face toward you, legs down: **E B C** on both; verify on the datasheet for your brand |
| 1 kΩ, 470 Ω, 100 kΩ × 2 | base resistor, LED resistor, divider | colour bands: brown-black-red, yellow-violet-brown, brown-black-yellow |
| coin motor, 5 mm green LED, 12 mm yellow button, WS2812 strip (cut 3 pixels) | UI | LED soldered into the strip (shows through the lid); bar lies in the middle-wall pocket; button (trunk B) + motor (trunk A, its own two wires) in the forearm module |
| GY-BNO08X | orientation | I²C address 0x4A with AD0/SA0 low, 0x4B with it high (datasheet); the bench prints which it finds and the firmware probes both. **Lives in the forearm module, not the box** |
| SEN0240 × 2 (plate + signal board + 3.5 mm cable) | EMG | boards in the forearm module, plates on their loop band; the Gravity cables are not used |
| JST-PH kit: 6-pin sockets × 2, 4-pin sockets × 2, 3-pin socket × 1, housings + crimp pins | every connector | box: PH6 + PH4 + PH3 in the walls; module: PH6 + PH4 stacked |
| 1.5" elastic strap, ≤ 22 mm elastic (loop band), M2 × 4/6/8 screws, M3 × 5/6 (the two signal boards), 10 M2 heat-set inserts | mounting | see PUCKS.md |
| Qi receiver + coil + ferrite | wireless charging | last thing you add |
| Kapton tape (amber) | insulation, heat-proof | around the cell's edges, over solder stubs, holds ferrite to coil and the coil to the cell (nothing sticks to the lid) |
| (optional, later) foil shield | conductive | only if the EMG trace is noisy: kitchen foil around the twisted EMG1/EMG2/GND trio with a bare wire under it to GND at the box end; **never near the Qi coil** |
| multimeter | your eyes | DC volts; also continuity (beep) for checking joints |

## 1. Power, without the Pico

Wire only: cell, switch, diode 1, the charger board, and the meter.

1. **Polarity first.** Meter across the cell's own plug: 3.6–4.2 V with red on the red lead. Negative = the leads
   are swapped at the plug; note which is really plus and go by the meter, not the colour, from here on.
2. **Charger board.** Cut the cell's plug off one lead at a time (never two bare ends loose). Cell + → **B+**, cell − → **B−**.
   Meter **OUT+ to OUT−**: the cell voltage. A Type-C cable in the board's own socket for a moment: red LED = charging.
   Pull it out again; that socket stays unused in the box. Continuity with the cell unplugged: **IN− ↔ OUT−** beeps
   (same net), **B− ↔ OUT−** does not (that is the protection FET). If B− beeps to IN− instead, stop and say so.
3. **Kill switch.** OUT+ → switch middle. Switch outer → diode 1 plain end. Meter from **diode 1 stripe end to OUT−**:
   switch on → cell minus ~0.3 V; switch off → 0 V.

**Pass:** correct polarity, OUT+ = cell voltage, red LED on USB, diode output follows the switch.

## 2. Pico alone, MicroPython, blink

1. Hold BOOTSEL, plug the Pico into the PC, drop the **MicroPython Pico W / Pico 2 W .uf2** on the RPI-RP2 drive.
2. Open the MicroPico terminal (VS Code) or any serial terminal. You should get `>>>`.
3. Type `from machine import Pin; Pin("LED", Pin.OUT).toggle()` — the onboard LED toggles. The Pico is alive.

## 3. Pico on battery power

1. Diode 1 stripe → Pico **pin 39 (VSYS)**. Charger **OUT−** → Pico **pin 38** (OUT−, not the cell lead: the protection FET sits between them). Nothing else.
2. Unplug USB, switch on: onboard LED behaviour as before when you run the toggle from a saved `main.py` (write a two-line blink `main.py` first, over USB).
3. Charger's 5 V input, two feeds meeting at **IN+**, each through its own 1N5817 with the stripe toward the board:
   Qi + → diode 2 → IN+, Qi − → IN−; Pico pin 40 (VBUS) → diode 3 → IN+. Switch **off**, coil on the pad: red LED =
   charging and the Pico's onboard LED stays dark. Switch on, still on the pad: the band runs from the battery while
   it charges; blue/green LED = full.
4. USB into the Pico, switch off: the Pico runs from USB (that is the programming state) and the red LED shows the
   cell charging through diode 3. Switch on: same, and the band's battery reading is live. Diode 1 keeps USB out of
   the cell by any path but the charger. Charge from a wall brick, not a laptop port: 1 A charge plus the Pico pulls
   a weak port down.

**Pass:** blinks on battery alone; USB runs it and charges; switch off on the pad = charging with the Pico dark.

What each state does: switch off + nothing plugged = dead, zero drain. Switch off + pad = charging, Pico dark.
Switch off + USB = Pico on (programming) + charging, battery reading shows 0 so the firmware knows the switch is
off. Switch on = band runs from the battery, and USB or the pad charge it meanwhile.

The band's battery path, for reference: cell → B+/B− → OUT+ → switch → 1N5817 → Pico pin 39; OUT− → Pico pin 38.
Never connect the cell straight to VSYS without the diode and then plug USB in: the Pico's internal diode would push
USB current into the cell uncontrolled.

## 4. Peripherals, one at a time, with `bench/band_bench.py`

Copy `band/software/bench/band_bench.py` to the Pico as `main.py` (or run it from MicroPico). It prints a status line
every 150 ms and runs a self-test on the button. Add parts in this order and watch the line change:

| add                 | wiring                                                                                     | what the bench script shows                                                        |
| ------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| **button**          | GP7 ↔ one leg, GND ↔ diagonal leg                                                          | `BTN 1` while pressed; tap = buzz attempt + pixel chase (nothing yet, that's fine) |
| **WS2812 (3 px)**   | +5V pad → 3V3 (pin 36), GND → GND, DIN → GP16                                              | self-test colours R G B W at boot; then pixels 0/1 meter the EMG                   |
| **motor circuit**   | GP13 → 1k → base; E → GND; 3V3 → motor → C; 1N4007 across the motor, stripe to 3V3         | tap the button: a 60 ms buzz. If it hums weakly, the transistor legs are swapped   |
| **green LED**       | 3V3 → 470 Ω → long leg; short leg → GND                                                    | on whenever the Pico is on (no code involved)                                      |
| **battery divider** | switch output (before the 1N5817) → 100k → GP28 → 100k → GND                                                           | `BAT 3.9x V` matches the meter on the cell within 0.05 V                           |
| **BNO08x**          | 3V3→VCC, GND→GND, GP4→SDA, GP5→SCL, GP6→INT, RST → VCC (jumper on the board), PS0 + PS1 + AD0 → GND, CS left open  | `IMU ok 0x4b`                                                                      |
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

Diagrams with every hole, wire and build order for the strip, the battery bay, the forearm module and the cables:
the Build tab of [viewer/index.html](viewer/index.html) (open it in a browser; the generator is hardware/cad/strip_map_svg.py).

### 7a. What goes on the strip, and where

- The Pico on its headers, rows 1–20, USB face flush with the row-1 end.
- Green LED standing in rows 21–22, third column in on the chest side, 1 mm off the board, long leg toward its 470 Ω,
  which lies flat beside it toward the centre. The lid's hole lands over the dome.
- The divider pair (100 k × 2), the motor driver (1 k / S8050), diode 1 (1N5817). The motor's 1N4007 is NOT on the
  strip: it sits across the motor's own tabs in the forearm module. Exact holes for everything: PARTS.md, "Strip map".
- Tall parts (anything on end, up to 4.5 mm) only on the two outer rows beside the Pico: rib side anywhere from
  20 mm before the strip centre to the free rows; chest side except under the LED (18 ± 5 mm). The CAD checks exactly these zones.
- Nothing else. The IMU, the EMG boards, the button and the motor are in the forearm module. Nothing is on the lid.
- Standoffs: the four drilled holes (rows 2 and 21, columns 1 and 10). Nip both USB-end corners of the board ~2 mm
  at 45° for the bay's rounded corners. Clip every lead 1.5 mm under the board.

### 7b. Soldering order

1. Pico headers, then the star ground blob at row 22, outer columns.
2. 470 Ω, then the LED (standing, 1 mm off the board).
3. The 100 k pair (top end to the switch's output side, not to the cell), 1 k, S8050, diode 1, at the holes in PARTS.md.
4. Flying leads off the strip: switch return off (22,5) 30 mm; charger OUT− 60; light bar GND / 3V3 / GP16 (3) 60 each;
   VBUS (pin 40 stub) → diode 3 → charger IN+ 60. Charger OUT+ → switch middle is a 110 mm lead between those two
   parts that never touches the strip. The Qi receiver's two wires never reach the strip: + → diode 2 → charger
   IN+, − → charger IN−.
5. Wall sockets: clip each socket's pins to 2 mm, solder 60 mm leads on, and solder those leads to the strip:
   PH6 = trunk A (3V3 GND EMG1 EMG2 MOT+ MOT−), PH4 = trunk B (SDA SCL INT BTN), PH3 = hand cord (TX RX GND).
6. Charger board on its two leads plus the Qi pigtail (1N5817 in the + wire, stripe toward the board); switch on its
   two; light bar on its three (its −X pads: GND, +5V, DIN).
7. Bench script again with everything dangling off the strip. Only then conformal coat the strip (mask the
   standoff holes and the LED).

### 7c. Box assembly, in this order (fit-checked in the CAD)

1. **Box onto the plate**: two M2×6 from inside the battery bay, down through the small floor bosses into the plate
   posts' inserts (the post sits inside the boss; the screw head pulls the boss's web onto the brass). Empty box, so
   the driver has room.
2. **Trunk A socket (PH6)** into the battery-side end-wall pocket, opening out; its leads run behind the battery ring
   and through the USB-end notch to the strip. Hot glue on top of the socket.
3. **Charger board** into its cradle: USB-C toward the triceps wall, pads toward the middle wall, cell leads already on
   B+/B− and coming back through the ring's lead notch. Kapton over it.
4. **Qi board** flat on the cradle's four bracket tops, parts up; its two output wires go to the charger's IN+ (through
   the 1N5817) and IN−, right beside it, not to the strip.
5. **Cell** into the ring, tape lip toward the charger, leads through the notch.
6. **Ferrite + coil** on the cell, ferrite down, a Kapton band round the cell holding both. Nothing sticks to the lid;
   it lifts straight off.
7. **Trunk B (PH4) and hand cord (PH3) sockets** into the strip-side end-wall pockets, hot glue.
8. **Strip** onto its four standoffs, four M2×4.
9. **Switch**, already on its two leads, down onto its shelf on the chest wall past the strip's +X end (ends between
   the two fins, nub through the slot), a dab of glue. Its OUT+ lead comes from the charger through the USB-end notch
   and along the strip's middle-wall edge; its return drops to (22,5) right beside it. Check it still throws before
   the glue sets.
10. **Light bar** into the middle-wall pocket, LEDs up, leads through the USB-end notch.
11. **Lid**: two M2×6 into the inserts. Both screws go in square to the strip-side facet, leaning toward the chest,
    not vertical.

### 7d. Tape

Kapton over the strip's solder side (standoff holes clear) → around the cell's four edges and the tape lip → once
round the charger board → coil: ferrite on the inner face, Kapton over both, a band round the cell → over the charger's
soldered wires before the Qi board goes on. All under 0.1 mm; the pockets allow for it. Trunk: twist EMG1/EMG2 with
a GND wire, braided sleeving over both trunk cables together (foil shield only if the bench shows noise).

## 8. Forearm ring and the cables

Build and wiring for the forearm module and the electrode frames are in [hardware/PUCKS.md](hardware/PUCKS.md).
Cables to crimp (PH housings on both ends; PH contacts take 24-30 AWG, insulation OD 0.9-1.5 mm - 30 AWG silicone is
fine, 30 AWG wire-wrap is too thin for the insulation tabs to grip):

Crimp recipe (Engineer PA-09): strip 2.5 mm, do NOT tin. Contact in the jaw with the open barrels facing the shaped
(upper) die. Conductor barrel in the **1.4** slot (1.6 for 24 AWG), then the insulation barrel in the **1.9** slot.
Bare copper only under the first pair of tabs, insulation only under the second, a sliver of copper visible between
them. Tug test every one before it goes in the housing. Contact into the housing with its little lance toward the
housing's windows until it clicks; a mis-seated one pushes back out when the plug mates. Pin 1 is the end with the
housing's polarising ramp; check colours against the PINOUT table before the second end goes on.

| cable | ends | length | notes |
|---|---|---|---|
| trunk A | PH6 ↔ PH6 | 25 cm | 3V3, GND, EMG1, EMG2, MOT+, MOT− - twist EMG1/EMG2 together with GND (that is the shielding for v1) |
| trunk B | PH4 ↔ PH4 | 25 cm | SDA, SCL, INT, BTN |
| hand cord | PH3 ↔ PH3 | as needed | TX, RX, GND, **crossed** (band TX → hand RX); HAND-WIRED mode |
| plate cables | 3.5 mm ↔ 3.5 mm | the kit's | one per electrode, plate jack → module wrist wall |

At the module the two trunk housings are glued face-to-face into one block (PH6 below, PH4 above, one tall
window); at the box they go into two different walls, so they stay separate there. Glue the module end **after**
a first plug-in so the pair sits square. Braided sleeving over both trunk cables together. ("Two walls" at the box
= the two halves of the +X end wall, battery bay and strip bay, either side of the middle wall.)

Bench test of the ring: plug the trunk into the box, run the stage-4 bench script; `IMU ok 0x4b` and both EMG
columns must behave exactly as they did on the breadboard. If `IMU` fails, it is SDA/SCL or INT swapped in trunk B.

## Safety, short version

- LiPo: never short the JST, never charge unattended the first time, never charge while worn. Warm is normal; hot is not.
- Check the cell's polarity with the meter before soldering it to B+/B−. Suppliers do not agree on red/black.
- Diodes backwards do nothing (fine) or short things (not fine). Stripe = the end current leaves from.
- The Pico's 3V3 pin can give ~300 mA total. Everything we hang on it adds up to ~150 mA. Don't add a servo to it.
