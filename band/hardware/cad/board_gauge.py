# agentcad run band/hardware/cad/board_gauge.py --label board_gauge --export stl
"""Hole gauge for the SEN0240 signal board (no calipers: print this, 10 minutes, before the module).

Row 1 - hole SPACING across the board: six stations, each a pair of slots 3.2 wide (across) x 5 long (along the
board), centre-to-centre 14.6 ... 16.6. Lay the board across a station, drop two M3 screws through its two mount
holes: the station where BOTH screws fall through freely is the spacing (the slots are loose along the board, so
only the spacing counts). Read the embossed number.

Row 2 - hole distance from the JACK end: a stop lip. Butt the board's jack end against the lip (jack up, it passes
through the gap). The +Y slot sits 5.3 from the lip (the caliper reading), the -Y slot 6.8 (the reading if it was
taken to the hole's edge, not its centre). Whichever screw drops in is the number; if neither, say which side of
the slot the screw lands on.
"""
from build123d import Box, Location, Align, Text, extrude, Axis

PLATE_L, PLATE_W, T = 64.0, 50.0, 1.6
SLOT_W, SLOT_L = 3.2, 5.0                      # M3 clearance across, loose along
SPACINGS = [14.6, 15.0, 15.4, 15.8, 16.2, 16.6]
DOWNS = {1: 5.3, -1: 6.8}                      # +Y slot / -Y slot distance from the lip face
ASSUMED_SPACING = 15.0

plate = Box(PLATE_L, PLATE_W, T, align=(Align.MIN, Align.MIN, Align.MIN))

# row 1: spacing stations along X, slots centred on y = 14
y1 = 14.0
for i, s in enumerate(SPACINGS):
    x = 6.0 + i * 9.5
    for sy in (-1, 1):
        plate -= Box(SLOT_L, SLOT_W, 10).moved(Location((x, y1 + sy * s / 2, 0)))
    plate += extrude(Text(f"{s:.1f}", font_size=2.6, align=(Align.CENTER, Align.CENTER)), amount=0.6).moved(
        Location((x, y1 + 12.0, T)))
    plate += extrude(Text(f"{s:.1f}", font_size=2.6, align=(Align.CENTER, Align.CENTER)), amount=0.6).moved(
        Location((x, y1 - 12.0, T)))

# row 2: the jack-end distance. Lip along Y at x = 10 (face toward +X), a gap in its middle for the jack body
y2 = 38.0
lip_x = 10.0
for sy in (-1, 1):
    plate += Box(1.5, 7.0, 2.0, align=(Align.MAX, Align.CENTER, Align.MIN)).moved(Location((lip_x, y2 + sy * 8.5, T)))
for sy, d in DOWNS.items():
    plate -= Box(SLOT_W, 6.0, 10).moved(Location((lip_x + d, y2 + sy * ASSUMED_SPACING / 2, 0)))
    plate += extrude(Text(f"{d:.1f}", font_size=2.6, align=(Align.MIN, Align.CENTER)), amount=0.6).moved(
        Location((lip_x + d + 3.0, y2 + sy * ASSUMED_SPACING / 2, T)))
plate += extrude(Text("jack end vs lip", font_size=2.4, align=(Align.MIN, Align.CENTER)), amount=0.6).moved(
    Location((lip_x + 14.0, y2, T)))
plate += extrude(Text("SEN0240 hole gauge", font_size=2.4, align=(Align.MIN, Align.CENTER)),
                 amount=0.6).moved(Location((27.0, 46.0, T)))                    # clear of the 5.3 slot and its label

show_object(plate, id="board_gauge", name="SEN0240 hole gauge")
