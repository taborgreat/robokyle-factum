# Forearm ring (strap-mounted)

Everything on the 1.5" elastic strap around Kyle's upper forearm. Source `cad/forearm.py` (run `forearm_run.py`,
check with `python band/hardware/cad/forearm.py`). Prints in `print/`, all PLA Tough:

| print | qty | where on the arm | holds |
|---|---|---|---|
| `electrode_frame` 39.6 x 38.3 | 2 (more later) | on the skin, on its OWN thin loop band: one on top of the forearm (extensors), one inside (flexors) | one dry electrode plate, bars down, 0.9 mm proud of the lip; the band lies across its back |
| `electrode_bar` 34 x 5 x 2 | 2 per frame | screwed over the band at each edge of the frame | clamps the band (squeezed 0.2 mm) so the frame cannot creep; 2 x M2x6 each, unscrew to lift the frame off for washing |
| `fa_module` 54 x 54 at the sleeve | 1 | on the strap, thumb side | both SEN0240 signal boards (one per facet), the BNO08x on the floor under the extensor board, both PH4 trunk sockets stacked in one pocket in the elbow wall |
| `fa_lid` | 1 | | nothing (no wires cross the lid) |
| `fa_backer` 54 x 54 | 1 | under the strap, under the module | the clamp plate |

Curvature: R_FA = 34 mm (a ~21 cm forearm; change one number and re-export if Kyle measures different). The frames
and the backer are curved on the skin side; the module is a two-facet tent like the band box, so each flat board
lies on its own facet and nothing wastes height.

## Cables (all plug-to-plug)

- the electrodes ride a separate light elastic (<= 22 mm wide, like the plate's own slots take) so Kyle can slide
  them onto the muscle without moving the module; the module keeps its own backer on the 1.5" strap
- electrode plate -> its own 3.5 mm cable -> the module's wrist wall (each board's jack faces that wall)
- module elbow wall -> ONE trunk plug: the two PH4 housings glued side by side face-to-face into a 2x4 block
  (A: 3V3 GND EMG1 EMG2 on the lower socket, B: SDA SCL INT RST on the upper), one window in the wall; at the
  band box the same two housings are glued side by side flat (that wall's window is wide, not tall)
- inside the module: each board's Gravity pins (GND VCC SIG, wires soldered under the board) go to the sockets;
  board A's three wires cross the rib through the notch at the elbow end; the IMU's six wires go to the upper
  socket + 3V3/GND. Everything is screwed: 2 x M2x4 per board A, 2 x M2x6 board B, 2 x M2x4 the IMU.

## Strap prep (hot nail: sealed holes)

- electrodes: nothing to cut - the closed loop band lies across the frame and the bars clamp it
- module: nothing to cut - the strap runs between the backer's two rails, under the module, and the two clamp
  screws sit just outside the strap's edges (45 mm apart)

## Assembly

1. Electrode: plate into the frame (bars through the window, jack up). Lay the closed loop band across the frame's
   back - it runs over the plate and presses it in - toward the elbow side of the frame (the jack lump is on the
   wrist side, clear of it). Drop a clamp bar over the band at each edge and screw it to the two bosses with M2x6:
   the band is squeezed 0.2 mm and cannot creep. To wash the band: two screws out on each frame, lift the frames
   off. Plug the 3.5 mm cable in; it runs along the arm to the module. Band: 20-22 mm elastic, sewn into a loop
   that is snug on Kyle's upper forearm (measure that too).
2. Module, in this order: (1) IMU - clip its header to ~2 mm, solder six 60 mm wires, screw it to its two posts in
   bay B (header edge toward the rib). (2) Sockets - solder 60 mm leads to two PH4 sockets, clip the pins to 2 mm,
   drop both into the elbow-wall pocket (lower = trunk A, upper = trunk B), hot glue on top. (3) Board A into bay A
   on its posts (jack end to the wrist wall), wire its Gravity pins, pass the three wires through the rib notch.
   (4) Board B over the IMU on its tall posts, wire it. (5) Backer under the strap with the strap between its rails,
   module on top, 2 x **M2x12 from the skin side** into the module's bosses (they pass beside the strap, not through
   it; the floor squeezes the strap 0.2 mm against the backer); lid on, 2 x M2x4. To wash: two screws out, slide
   the module off the strap.

## Assumed - check against the parts

- electrode plate 36 x 23.3 x 1.11, bars 14.5 x 5.8 at 11.3 pitch and 1.5 proud, jack on the BACK overhanging ~2 mm
- signal board 40 x 22, holes 3.0 at 2.7 in / 5.3 from the jack end, parts in its middle <= 2.5 tall
- BNO08x breakout 25.5 x 15.8 with a header on one long edge (clipped); **mount holes assumed** 2.5 mm in from the
  two corners on the edge opposite the header - if the board has none, snip the posts and glue it
- strap 1.5 mm thick; forearm radius 34
