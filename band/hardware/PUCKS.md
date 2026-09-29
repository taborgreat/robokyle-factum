# Forearm ring (strap-mounted)

Everything on the 1.5" elastic strap around Kyle's upper forearm. Source `cad/forearm.py` (run `forearm_run.py`,
check with `python band/hardware/cad/forearm.py`). Prints in `print/`, all PLA Tough:

| print | qty | where on the arm | holds |
|---|---|---|---|
| `electrode_frame` 48 x 38.3 | 2 (more later) | on the skin, on its OWN thin loop band: one on top of the forearm (extensors), one inside (flexors) | one dry electrode plate, bars down; the plate's middle stands 1 mm proud of the frame's face and the bars 2.5 mm, so they reach the skin before the frame's curved edges do; the band lies across its back |
| `electrode_cover` 48 x 38 x 1.6 | 1 per frame | screwed over the frame, 4 x M2x6 | holds the plate in; the closed loop band threads down through one slot, under the cover's pad (which presses it onto the plate), up through the other slot; notch for the jack. Four screws out = frame off the band for washing |
| `fa_module` 54 x 64 at the sleeve | 1 | on the strap, thumb side | both SEN0240 signal boards (one per facet), the BNO08x under the extensor board, the **yellow button** sunk in the 16 mm middle rib (cap through the lid's flat crest), the **coin motor** in a pocket beside it (on 1.6 mm of floor, no hole to the strap), PH6 + PH4 trunk sockets stacked in the elbow wall |
| `fa_lid` | 1 | | nothing (no wires cross the lid) |
| `fa_backer` 54 x 64 | 1 | under the strap, under the module | the clamp plate; 26 sewing eyelets round its edge so the module can be sewn to the sleeve on its own - the electrodes stay on their separate loop band |

Curvature: R_FA = 34 mm (a ~21 cm forearm; change one number and re-export if Kyle measures different). The frames
and the backer are curved on the skin side; the module is a two-facet tent like the band box, so each flat board
lies on its own facet and nothing wastes height.

## Cables (all plug-to-plug)

- the electrodes ride a separate light elastic (<= 22 mm wide, like the plate's own slots take) so Kyle can slide
  them onto the muscle without moving the module; the module keeps its own backer on the 1.5" strap
- electrode plate -> its own 3.5 mm cable -> the module's wrist wall (each board's jack faces that wall)
- module elbow wall -> ONE trunk plug: PH6 (below: 3V3 GND EMG1 EMG2 BTN MOTOR) and PH4 (above: SDA SCL INT RST)
  glued face-to-face into one block, one window in the wall; at the band box they go into two different walls
- inside the module: each board's Gravity pins (GND VCC SIG, wires soldered under the board) go to the sockets;
  board A's three wires cross the rib through the 5 x 5 passage at the elbow end (it goes straight through both rib walls); the IMU's six wires go to the upper
  socket + 3V3/GND; the button's two wires (BTN, GND) and the motor's two (3V3, MOTOR) run down the 4 x 4 tunnel
  in the rib's core and out through the 5 x 5 hole in the rib's wall into bay B, right behind the socket block,
  to the PH6. Board A's three wires use the same passage from the other side. Everything is screwed: 2 x **M3x5** per board A
  (M3x6 only with a washer under the head - the post is 2.8 tall and the thread hole stops 0.4 above the strap), 2 x M3x6
  board B, 2 x M2x4 the IMU. Button: clip two legs flush and the other two to 1.5 mm, solder the wires sideways, drop it in its
  pocket cap-up; the lid's cap hole holds it. Motor: solder the 1N4007 across its two tabs first, standing up along the tab slot, stripe on the lead that will be
   3V3 (trunk A pin 1); leads up the tab slot into the tunnel and out the wall hole, then peel its pad and press it onto
   the pocket floor, tab toward the button.

The two jack windows and the trunk window are open at the top: the module's end walls stop at the lid's parting
line, and the lid's skirt closes each notch when it is on. That is by design (a closed window would leave a 1 mm
bridge of wall above it, which does not print).

## Strap prep (hot nail: sealed holes)

- electrodes: nothing to cut - the closed loop band lies across the frame and the bars clamp it
- module: nothing to cut - the strap runs between the backer's two rails, under the module, and the two clamp
  screws sit just outside the strap's edges (45 mm apart)

## Assembly

1. Electrode: plate into the frame (bars through the window, jack up). Thread the closed loop band down through
   one slot of the cover, across, and up through the other (the band sits toward the elbow side; the jack lump is
   on the wrist side in its notch). Set the cover on the frame - the band now lies on the plate's back under the
   cover's pad - and screw it down with 4 x M2x6. To wash: four screws out, cover off, frame off. Plug the 3.5 mm
   cable in; it runs along the arm to the module. Band: 20-22 mm elastic, sewn into a loop that is snug on Kyle's
   upper forearm (measure that too). Not the 1.5" strap: that would run over the jack lump.
2. Module, in this order: (1) IMU - clip its header to ~2 mm, solder six 60 mm wires, screw it to its two posts in
   bay B (header edge toward the rib). (2) Sockets - solder 60 mm leads to the PH6 and the PH4, clip the pins to
   2 mm, drop both into the elbow-wall pocket (PH6 below = trunk A, PH4 above = trunk B), hot glue on top. (2b)
   Motor leads and button wires down the rib tunnel and out the wall hole to the sockets, motor into its pocket,
   button into its pocket.
   Screws: the two ridge bosses are drilled through - M2x12 from the skin side (backer + strap + 9.5 mm of boss)
   and M2x4 from the top for the lid; no screw spans the whole height. (3) Board A into bay A
   on its posts (jack end to the wrist wall), wire its Gravity pins, pass the three wires through the rib passage into bay B.
   (4) Board B over the IMU on its tall posts, wire it. (5) Backer under the strap with the strap between its rails,
   module on top, 2 x **M2x12 from the skin side** into the module's bosses (they pass beside the strap, not through
   it; the floor squeezes the strap 0.2 mm against the backer); lid on, 2 x M2x4. To wash: two screws out, slide
   the module off the strap.

## Assumed - check against the parts

- electrode plate 36 x 23.3 x 1.11, bars 14.5 x 5.8 at 11.3 pitch and 1.5 proud, jack on the BACK overhanging ~2 mm
  (the plate rests on the frame's lip along its two long edges only; its middle is open to the skin)
- signal board 40 x 22, holes 3.0 at **3.25 in from the sides (15.5 apart; measured by eye at 3 to 3.5, no datasheet
  figure)**. The posts' 2.6 holes have a countersink, so an M3 still finds its way in if the real spacing is 15.0 or
  16.0; drive the second screw while pressing the board toward it. The board sits 0.8 off the wrist wall, so the
  jack-end distance may be up to 1 mm less than 5.3 without a change. Parts in its middle <= 2.5 tall
- BNO08x breakout 25.5 x 15.8 with a header on one long edge (clipped); **mount holes assumed** 2.5 mm in from the
  two corners on the edge opposite the header - if the board has none, snip the posts and glue it
- strap 1.5 mm thick; forearm radius 34
