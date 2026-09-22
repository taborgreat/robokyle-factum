Robo Kyle claw gripper v1 - printed parts (parametric OpenSCAD + STLs)

LAYOUT (X = forward toward the fingers, Y = across, Z = up)
  body.stl      145 x 72 x 43 mm PETG block. Front: gear deck on top with the STS3215 standing in a pocket, its shaft
                at (pivot_x, y=-20); an idler pivot at (pivot_x, y=+20) on a 3 mm pin with a top bearing seat.
                Rear: open bay, divider rib down the middle: battery (+Y side), Pico + driver board + BMS + buck (-Y side,
                Pico on four M2 standoffs). Rear wall: USB-C charge slot and kill-switch slot. Rear face: 4 M3 heat-set
                holes for the cuff stub.
  gear_drive.stl  module-2, 20-tooth gear that bolts to the servo horn (horn recess + 4 screw holes); 2 M3 holes at the rim for a finger.
  gear_idler.stl  same gear on two 3x8x3 bearings over the idler pin; 2 M3 holes for the other finger.
  finger.stl    fin-ray finger, print in TPU 95A lying flat: 80 long, 26 base, 10 tip, 18 wide, 1.4 walls, 6 ribs.
                Base tab with 2 M3 holes bolts to a gear rim. Slot along the inner face takes a pad. Print two (one mirrored in the slicer).
  pad.stl       TPU grip pad, slides into the finger slot; roughen the face. Cast silicone pads later use the same slot.
  lid.stl       covers the rear bay.
  cuff_stub.stl bolts to the rear face (4x M3), presents 4x M4 holes for whatever cuff you build.

HOW IT MOVES
  Servo turns the drive gear; the drive gear turns the idler; each gear carries a finger; both fingers swing symmetrically.
  Gear centers 40 mm apart. Set servo angle limits so the fingers stop just short of touching and just short of full open.

PRINT
  Body, gears, lid, stub: PETG, 4 walls, gears 100% infill. Fingers, pads: TPU 95A, slow, external spool.

VERIFY BEFORE PRINTING THE BODY (top of claw.scad)
  servo_l/w/h, servo_ear_l/w, servo_shaft_x   measure the STS3215 and its ear holes
  servo_horn_d + horn screw spacing            measure the metal horn
  batt_l/w/h, drv_l/w/h                         measure the pack and the driver board
  Print the gears and one finger first; they need no measurements.

CONDUCTIVE TIPS
  Each finger has a 2 mm groove along its outer wall from the pad pocket to a cross hole in the base tab; the body has
  2.5 mm pass-throughs in the front wall beside each pivot and in the rear face beside the stub; the stub has two more.
  Run a 28 AWG wire tip -> groove -> tab -> front hole -> bay -> rear hole -> stub -> conductive patch in the cuff liner.
  Leave a slack loop at the pivot. Pad in conductive TPU or wrapped in conductive fabric, contact face at least 7 mm.

ELECTRONICS (all in the rear bay)
  pack -> BMS -> kill switch -> node feeding: driver board power terminal, buck converter in, charger board BAT
  buck 5 V -> Pico VSYS; driver TX/RX/GND -> Pico UART; servo -> driver socket; charger USB-C through the rear wall
  Endpoints on the Pico: open, close?force=, stop, estop, keepalive (500 ms watchdog opens). Torque limit and load from the servo.
