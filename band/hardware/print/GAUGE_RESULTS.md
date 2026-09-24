# Fit gauge results (fill in, send back)

Print `fit_gauge.stl` flat, labels up. Chamfered corner = origin. For each row: push the part in square, note the
first size it goes into **freely** (no force). Free = drops in with a wiggle. If it only goes in with force, take
the next size up. Write "none" if nothing fits, "all" if even the tightest fits.

## Stepped slots (top edge: BATT, STRIP, PICO; bottom edge: IMU, CHG, SW, EMG)

Push the part in edge-first. The slot narrows in 4 steps going in: 1 = loosest (mouth), 4 = tightest (bottom).
Report the deepest step the part reaches freely (1-4).

| slot  | part                                                 | deepest free step (1-4)                                                                                                                                                                            |
| ----- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| BATT  | battery (30.5 mm side)                               | goes all the way with maybe another 4 slots of clearance but the last slot is pretty close, and note the battery shape in image im sending in prompt as it has a lip accross in yellow for chip in |
| STRIP | perfboard strip (25 mm side)                         | the neastest perfoboard stip i have ill take photo of it may be too big but it fits exactly in the largest battery hole ill send photo                                                             |
| PICO  | Pico W (21 mm side)                                  | stops at hole 2/3                                                                                                                                                                                  |
| IMU   | GY-BNO08X (14.5 mm side)                             | stops at very frist hole right at start, perfect                                                                                                                                                   |
| CHG   | charger module (6.5 mm side)                         | barely dosnt fit, but also maybe by like 1mm or a good amount cmpared to others                                                                                                                    |
| SW    | slide switch body (3.7 mm side, pins out of the way) |                                                                                                                                                                                                    | perfect fit at very last hole |
| EMG   | SEN0240 board (22 mm side) — skip if not arrived     |                                                                                                                                                                                                    |

## Round holes (report the first hole it goes into, counting from the left = smallest)

| ladder | part                                                                                                                                         | first free hole (1..n)                                                           |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| LED    | 5 mm green LED dome (4 holes)                                                                                                                | the smallest hole is best for green LED                                          |
| MOT    | coin motor, 10 mm (3 holes)                                                                                                                  | coin motor has issue it fits into biggest hole but small module ull see in photo |
| M2     | M2 screw: smallest hole it BITES into when turned by hand (4 holes) the biggest hole is fine but the 3rd works too just a little tighter     |                                                                                  |
| INS    | M2 heat-set insert, sits in the hole before heating (3 holes) i htink it would work for the small one and middle but the lsat one is too big |                                                                                  |

## Rectangular slots (first free one from the left)

| ladder | part                                      | first free (1..3)                                                                                                                                                                                                                                                                                                                 |
| ------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAP    | yellow button cap (3 squares)             | the smallest one is best                                                                                                                                                                                                                                                                                                          |
| SWB    | slide switch body, flat, nub up (3 slots) | smallest hole for sure                                                                                                                                                                                                                                                                                                            |
| NUB    | switch nub with room to slide (3 slots)   | i dont get but the smallest works just too high of a wall                                                                                                                                                                                                                                                                         |
| PH2    | JST-PH 2-pin plug housing (3 slots)       | the smallest hole fits the female side through exact, but the male side doesnt connect through it biggest hole                                                                                                                                                                                                                    |
| PH3    | JST-PH 3-pin plug housing (3 slots)       | biggest hole, but also could be a little shorter vertically as it fits width wise with a bit of height above it. actually nevermind i forgot its two halves. the small female half fits through with vertical space, but i cant plug in the male half because its too wide (see photo from prompt) so it seemsto need to be wider |

Also useful: a photo of the printed gauge with the parts sitting in their slots.
