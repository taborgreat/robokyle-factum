# Parts, measurements and the decisions made for them

Everything that was measured on the real parts, and every fit rule that came out of the prints, in one place so
the next build (and the claw) starts from numbers instead of guesses. The CAD reads the same numbers from
`hardware/cad/rk_parts.py` (`DIM`, with a source flag: **M** caliper, **G** gauge print, **P** learned from a print,
**D** datasheet, **?** guess). If a number here and in `rk_parts.py` disagree, the code wins and this file is stale.

## Printer and material rules (Bambu, PLA Tough)

| rule | value | how it was learned |
|---|---|---|
| rigid part in a pocket, clearance per side | 0.5 mm | slots print ~0.4 undersize (G) |
| soft cell in its ring, clearance per side | 0.7 mm | (P) |
| plug window through a wall | plug housing + 0.8 mm wide, + 0.85 tall | first windows at "gauge slot" size were too narrow (P) |
| socket pocket behind a wall | socket + 0.5 mm | (P) |
| M2 thread-forming hole | 2.0 mm | bites by hand, holds (G) |
| M3 thread-forming hole | 2.6 mm, 0.6 mm countersink at the mouth | lets the screw find a hole 0.3 off |
| M2 heat-set insert hole (3.5 OD × 4 long brass) | 3.4 mm, 4.6 deep | 3.2 held but only started crooked (P) |
| M2 clearance hole | 2.3 mm | |
| M2 head counterbore | Ø4.2 × 1.4 deep | pan head is 3.8 × 1.3, so it sits 0.1 below the surface |
| 5 mm LED hole | 5.0 mm | press fit as printed (G) |
| 12 mm button cap hole | 12.6 mm | 12.4 was "best" on the gauge, 12.6 leaves play (G) |
| minimum wall next to a hole | 1.5 mm | |
| horizontal bridge over a window | avoid; open the window up to the lid's parting line instead | 1 mm bridges printed as dangling threads (P) |
| solid gap between two features | ≥ 1.0 mm or merge them | 0.3 mm air slivers print as ragged blobs (P) |
| lid seat | wall tops meet the lid underside AND the skirt sits on the parting step, both at nominal | any designed gap (0.2 was tried under the walls, then under the skirt) shows as a line of light (P) |
| skirt zone | built per row frame so it leans with the walls | a floor-width box missed the outer half of every end wall (P) |
| blind hole under a mating face | cut the hole 20 mm past the surface, never end it at the nominal top | a hole ending 0.2 under a face that later grows to meet it leaves a skinned mouth (P) |
| two tilted half-boxes forming a tent | overlap them past the centre by more than the lean shifts them at crest height | 12 mm of overlap left a 2 mm slot along the module lid's crest; 30 poked out below the walls; 16 is right (P) |
| filament | PLA Tough for the band, PETG for the claw | clearances above were measured in PLA Tough |

## Electronics, as measured

| part | what I have | measured | notes / decisions |
|---|---|---|---|
| Pico 2 W (band), Pico W (claw) | | 51 × 21 × 1.0; micro-USB receptacle 8 × 5.6 × 2.8, overhangs the board 1.3; mount holes Ø2.1 at 47 × 11.4 | soldered on the perf by its header pins (2.5 mm base), USB face flush with the strip end |
| micro-USB cable plug | the cable in hand | overmold 19.9 long × 10.7 wide × 7.5 tall; metal shell 7.5 × 6.85 × 1.9 | wall hole 9.0 × 3.6 rounded r1.0; the receptacle nose sits 0.8 inside the hole |
| perf strip | ELEGOO 4 × 6 cm double-sided perf, snapped | 10 columns × 22 rows, 57.0 × 29.9 × 1.6 (M); solder stubs 1.5 below | Pico on rows 1–20 (USB at the row-1 end), rows 21–22 free. Standoff holes drilled Ø2.2 at columns 1 & 10, rows 2 & 21 = ±24.13 × ±11.43 from the board centre. All four used. Nip both USB-end corners ~2 mm at 45° |
| LiPo cell | EEMB 803048, 1200 mAh, JST-PH plug, own protection board under the tape lip | 48.1 × 29.65 × 8.3 (M); tape lip 3.7 thick; leads out of the lip end | ring pocket + 0.7/side and 2 mm longer at the lip end, lead notch 10 wide; sits on 1.5 mm foam; **check the JST polarity with the meter before the first plug-in, one supplier's red landed on the wrong pin** |
| charger board | AITRIP TP4057 1 A Type-C with protection (Amazon 20-pack) | board 16.8 × 12.1; 18.35 long with the USB-C shell; 4.2 tall with it (M) | pads B+ B− / OUT+ OUT− / IN+ IN−. Cell on B+/B− (through a PH2.0 pigtail so it stays pluggable). OUT+ → switch, OUT− is the ground (protection FET in it), IN+ ← Qi + through a 1N5817 and ← Pico VBUS through another 1N5817 (both stripes toward the board), IN− ← Qi −. PROG 1 kΩ = 1 A; 2 kΩ = ~500 mA (optional). Lies flat, USB-C toward the triceps wall, pads toward the middle wall; the Qi board rests on the cradle's four bracket tops |
| (retired) SunFounder Li-po charger for Pico | from the Kepler kit | 20 × 7, pads VBUS / VSYS / GND, PH2.0 socket | LTC4054 + one B5819 diode, no protection, no boost. Its diode died after a reversed cell plug-in. Not used |
| (claw) 2S–4S boost charger | CN3302 board, Type-C, jumpers 2S / 1 A | | for the claw's 2S pack only. **Never on a 1S cell** (it outputs 8.4 V) |
| slide switch | SS12D00 style, 3 pins | body 8.6 × 3.7 × 3.6, nub 1.5 × 1.5 × 3.0, travel 2, pins 3.5 below (?) | pocket 9.2 × 4.3, slot 6 × 3 (G); glued between two 0.7 mm fins on the chest wall, nub through the wall |
| tactile button | 12 × 12 with square yellow cap | body 12 × 12 × 7.3, cap 12 × 12 × 4 r1.5, legs at 12.5 × 5.0 pitch, 3.5 below | cap hole 12.6; two legs clipped flush, two to 1.5 mm, wires soldered sideways; lives in the forearm module's rib |
| green LED | 5 mm | dome 5.0, flange 5.8 × 1.0, body 8.7, legs clipped to standoff + strip + 1.5 | soldered into the strip at rows 21–22, third column in on the chest side; 470 Ω from 3V3 |
| WS2812B strip | 60/m, 10 mm wide FPC | pitch 16.67, LED 5 × 5 × 1.6 on 1.0 FPC | 3 pixels, lies in the middle-wall pocket, powered from 3V3, GP16 |
| coin motor | 10 mm, 1027 type | Ø10 × 3.4, tab 4 wide, leads 15 | blind pocket Ø10.8 in the module's rib, 1.6 mm floor under it; S8050 low-side switch, 1N4007 across it |
| IMU | GY-BNO08X breakout | 25.5 × 15.8 × 1.6, parts 2.3 tall, header pins 8.4 (clipped to ~2) | on 2.5 mm posts under board B; mount holes **assumed** 2.5 in from the two corners opposite the header; I²C 0x4A with SA0/AD0 low, 0x4B high (firmware probes both) |
| EMG signal board | DFRobot SEN0240, ×2 | ~40 × 22 × 1.2; parts ≤ 6 tall at the connector; 3.5 mm jack one end, Gravity PH2.0 3-pin the other; mount holes Ø3.0, 5.3 from the jack end, **3.25 in from the sides (15.5 apart, read by eye at 3–3.5; a first print at 2.7 in was ~1 mm too wide)** | M3 posts Ø6.5, 2.6 holes + countersink; board sits 0.8 off the wrist wall; wires soldered under the Gravity pins |
| EMG electrode plate | SEN0240 dry electrode | 36 × 23.3 × 1.11; three bars 14.5 × 5.8 at 11.3 pitch, 1.5 proud on the skin side; jack on the back 14.14 long from 23.82 in, 5.57 tall, overhangs ~2 | frame pocket 36.2 × 23.3+, plate 1 mm proud of the curved frame face, bars 2.5 proud; cover screwed on with 4 × M2×6 |
| 3.5 mm plate cable | the kit's | plug Ø6.2, ~22 long past the board | jack windows 6.5 + 1 wide × 5.5 + 1 tall, rounded r1 |
| Qi receiver | Zerone 5 V 1 A | oval coil 43.75 × 25.3 × 1.0 + 0.6 ferrite; board 25.2 × 14.6, 2.0 with parts | coil on the cell under the lid (2 mm air), ferrite toward the electronics, Kapton band round the cell (nothing sticks to the lid); board on the charger cradle's bracket tops; output + → 1N5817 → charger IN+, − → charger IN− |
| JST-PH headers (the pin side, in the walls) | EGSCST kit: straight top-entry PCB headers B*B-PH-K-S | width (n−1)×2 + 4.1: 2p 6.1, 3p 8.0, 4p 10.0, 6p 14.0; 4.5 thick; 6.0 tall; pins 3.4 straight out the back | sit on their backs in wall pockets (open top, back posts, pin slot); pins clipped to 2 mm, wires soldered on; hot glue on top |
| JST-PH housings (the crimped-contact side, on the cables) | same kit, PHR-n | 3p 8.0, 4p 10.0, 6p 14.0 wide × 4.75 tall (M 2026-09-25) | wall windows 8.8 / 10.8 / 14.8 × 5.6 |
| crimp contacts | SPH-002T-P0.5S, loose | for 24–30 AWG, insulation 0.9–1.5 | Engineer PA-09: 1.4 slot conductor, 1.9 slot insulation; strip 2.5, no tinning |
| wire | 30 AWG (inside the box), 26–28 AWG silicone for cables | | 30 AWG wire-wrap is too thin for the PH insulation tabs |
| M2 heat-set inserts | 3.5 OD × 4 long, brass | | 4 in the band: 2 box lid bosses, 2 plate posts. None in the forearm parts |
| screws | M2 × 4 / 6 / 8 / 12 pan; M3 × 5 / 6 | | M2×6 lid and cover screws; M2×4 lid of the module and IMU; M2×12 module clamp; M3×5 board A, M3×6 board B |
| transistor / diodes / resistors | S8050 NPN (E B C, flat face toward you); 1N4007 (motor); 1N5817 × 3 (cell → VSYS, Qi + → charger IN+, Pico VBUS → charger IN+); 1 k, 470 Ω, 100 k × 2 | | S8550 is the PNP twin, do not use it in the low-side switch |

## Body and strap numbers

| item | value | note |
|---|---|---|
| upper-arm radius under the band | 44 mm | box and plate curvature |
| forearm radius under the module | 34 mm | **guess from a photo, ~21 cm around**; change `R_FA` and re-export if measured different |
| main strap | 1.5 in (38.1) elastic nylon, 1.5 thick | module clamp screws sit just outside it, 45 mm apart |
| electrode loop band | ≤ 22 mm elastic, sewn into a snug loop | threads through the cover's 24 × 3 slots |
| plate | sewn to the sleeve through radial eyelets; posts rise 2.9 into floor bosses; M2×6 from inside | inserts in the plate posts, entered from the post top (inside), nothing on the skin side |
| module backer | 2.4 thick, two rails for the strap, 26 sewing eyelets | clamp screws M2×12 from the skin side, heads sunk in counterbores; no inserts |

## Which way every fastener goes (nothing metal on the skin side except two sunk heads)

- Band box lid: 2 × M2×6 from the top into inserts in the box's bosses (both screws go in square to the strip-side facet, leaning toward the chest).
- Box to plate: 2 × M2×6 from inside the battery bay, down into inserts in the plate's post tops.
- Strip: 4 × M2×4 into thread-formed holes in the floor standoffs.
- Forearm module lid: 2 × M2×4 from the top into the ridge bosses.
- Module to backer: 2 × M2×12 from the skin side up through the backer into the ridge bosses (thread-formed, 9.5 mm engagement); the heads sit in Ø4.2 × 1.4 counterbores on the backer's skin face, 0.1 below it. Use pan heads (1.3 tall), not socket caps (2.0 tall, would stand proud).
- Boards in the module: M3 into the posts from above; IMU: M2×4.
- Electrode cover: 4 × M2×6 from the outside into the frame's bosses; the frame's skin side is plain plastic.

## Strip map (exact holes, as built)

**How to read a hole.** Look down at the top of the strip with the USB end at the top (away from you). Column 1
is top-left, column 10 top-right, rows 1 to 22 from the USB end. The Pico's pin 1 (GP0) is at (1,2) and its pin
40 (VBUS) at (1,9): pins 1–20 run down column 2 (pin = row), pins 40–21 run down column 9 (pin = 41 − row).
The lid's LED hole is over column 8, so in the box the **right-hand side (columns 9–10) faces the chest wall** with
the switch fins, and the left-hand side (columns 1–2) faces the middle wall, where the charger, trunk A and light
bar wires come through the notch. Holes are written (row, column).

Rules: parts go in from the top and are soldered underneath, leads clipped to 1.5 mm. Wires never get a hole: tin
the wire and lay it along the stub of its pin or part leg on the underside, one joint. Underside wires cross in the
bare lanes (columns 3–8 under the Pico), never over a stub. Every hole in columns 1 and 10 has a Pico pin 2.5 mm
away: keep those joints small. Standing parts only on column 1; column 10 stays flat (switch rows 12–17, LED rows 17–20).

| part | holes | notes |
|---|---|---|
| Pico | rows 1–20, columns 2 and 9 | USB face flush with the row-1 edge; header body flat on the strip |
| green LED | long leg (21,8), short leg (22,8) | flange 1 mm above the board |
| 470 Ω | (21,4) → (21,6), flat on top | underside solder run (21,6)→(21,7)→(21,8) to the LED's long leg |
| diode 1, 1N5817 | stripe end (22,2), plain end (22,5), flat on top | stripe toward column 1 |
| R1 100 k (divider top) | (4,10) → (7,10), flat on top | (4,10) is the switch-output tap |
| R2 100 k (divider bottom) | (7,10) → (10,10), flat on top | its top leg shares hole (7,10) with R1's leg: twist the two legs together |
| divider midpoint | underside bridge (7,10)↔(7,9) | (7,9) is GP28 |
| S8050 | E (13,1), B (14,1), C (15,1), standing | flat face away from the Pico (toward the board's edge); E is the leg nearest the USB end |
| emitter to ground | underside bridge (13,1)↔(13,2) | (13,2) is a GND pin |
| 1 kΩ | one lead soldered to the base leg 3 mm above the board, body lying toward the far end on the outboard side of the C leg, other lead in (17,1) | underside bridge (17,1)↔(17,2): (17,2) is GP13, the motor pin |
| 3V3 point | underside bridge (5,9)↔(5,10) | (5,9) is 3V3; (5,10) sits under R1's body and is free underneath |

| wire | from | to | length |
|---|---|---|---|
| charger OUT− | charger | pin 3 stub (3,2) | 60 |
| charger OUT+ | charger | switch middle | 60 (never touches the strip) |
| switch outer | switch | diode 1 plain-end stub (22,5) | 60 |
| VSYS | diode 1 stripe stub (22,2) | pin 39 stub (2,9) | 60, underside, diagonal under the Pico |
| divider tap | diode 1 plain stub (22,5) | R1 top stub (4,10) | 50, underside |
| divider ground | R2 bottom stub (10,10) | pin 33 stub (8,9) | 10, underside |
| LED supply | 470 Ω far stub (21,4) | pin 36 stub (5,9) | 45, underside |
| LED ground | LED short-leg stub (22,8) | pin 23 stub (18,9) | 12, underside |
| VBUS → charger | pin 40 stub (1,9) | 1N5817 (stripe toward the charger) → charger IN+, meeting the Qi diode there | 60 |
| light bar GND | bar −X pad | pin 8 stub (8,2) | 60 |
| light bar +5V | bar −X pad | pin 36 stub (5,9), with the LED supply | 60 |
| light bar DIN | bar −X pad | pin 21 stub (20,9) = GP16 | 60 |
| trunk A pin 1, 3V3 | PH6 header | (5,10), the 3V3 point | 60 |
| trunk A pin 2, GND | PH6 header | pin 8 stub (8,2), with the bar GND | 60 |
| trunk A pin 3, EMG1 | PH6 header | pin 31 stub (10,9) = GP26 | 60 |
| trunk A pin 4, EMG2 | PH6 header | pin 32 stub (9,9) = GP27 | 60 |
| trunk A pin 5, MOT+ | PH6 header | (5,10), the 3V3 point, with trunk A's 3V3 | 60 |
| trunk A pin 6, MOT− | PH6 header | S8050 C stub (15,1) | 60 |
| trunk B SDA / SCL / INT / BTN | PH4 header | pins 6, 7, 9, 10 stubs = (6,2) (7,2) (9,2) (10,2) | 60 |
| cord TX / RX / GND | PH3 header | pins 1, 2, 18 stubs = (1,2) (2,2) (18,2) | 60 |

Pins 36 and 8 and the 3V3 point (5,10) each take two wires: tin the two ends together, then one joint on the stub. Diagram of both sides: [hardware/strip_map.html](hardware/strip_map.html), rebuilt by python band/hardware/cad/strip_map_svg.py.
