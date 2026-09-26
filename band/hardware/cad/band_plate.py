"""Sewn plate under the cuff box: a PLATE_T-thick shell on the arm cylinder, a low rim the box drops into,
two heat-set insert bosses on the ridge line (the lid screws pass through the box floor into them), and
sewing eyelets around the margin. The box floor gets matching holes for the bosses (see band_box.plate_boss_holes).

    agentcad run cad/band_plate_run.py --label band_plate --export stl
"""
import math
from build123d import Box, Cylinder, Location, Align, Axis
import band_box as bb
from band_box import R, PLATE_T, IN_L, R_FLOOR, Y_POST, arm_cyl, outer_form, on_row

RIM_H, RIM_T, RIM_CLR = 1.5, 1.2, 0.3      # rim around the box footprint
MARGIN = 4.5                                # sewing margin outside the rim
EYELET_D, EYELET_PITCH = 2.0, 8.0
BOSS_D = bb.PLATE_POST_D                    # posts up through the box floor; insert on top; M2x6 from inside the box
BOSS_H = R_FLOOR + bb.PLATE_POST_UP          # post top just above the box floor
INSERT_HOLE_D, INSERT_DEPTH = bb.DIM["m2"]["insert_hole_d"], 4.6     # M2 heat-set insert (4.0 long) + 0.6 for the melt to go
BOSS_X = IN_L / 2 - 3.5                     # same as the box's ridge screws


def band(dr0, dr1):
    """Shell between two arm radii, unbounded in x/y (clip with a footprint)."""
    return arm_cyl(dr1) - arm_cyl(dr0)


def plate():
    foot = outer_form(inset=-(RIM_CLR + RIM_T + MARGIN), arm_cut=False)     # plate footprint (grows ends + sides)
    p = foot & band(0, PLATE_T)
    rim = (outer_form(inset=-(RIM_CLR + RIM_T), arm_cut=False) - outer_form(inset=-RIM_CLR, arm_cut=False)) & band(PLATE_T - 0.01, PLATE_T + RIM_H)
    p += rim
    for sx in (-1, 1):
        p += Cylinder(BOSS_D / 2, BOSS_H + 5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((sx * BOSS_X, Y_POST, -5))) & band(-0.01, BOSS_H)
        p -= Cylinder(INSERT_HOLE_D / 2, INSERT_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
            Location((sx * BOSS_X, Y_POST, BOSS_H + 0.01)))
    # eyelets: 2 mm holes drilled radially (each at its own arm angle, so every one goes straight through),
    # every 8 mm along both long sides and both ends, none inside the corner rounds, plus one on each corner's diagonal
    import math as _m
    slab = foot & band(0, PLATE_T)
    bbx = slab.bounding_box()
    half_l, half_w = bbx.size.X / 2, bbx.size.Y / 2
    corner = bb.CORNER_R + RIM_CLR + RIM_T + MARGIN          # the plate outline's corner radius
    def eyelet(x, y):
        """Radial 2 mm hole at global (x, y): rotate a vertical rod by the arm angle at that y."""
        rod = Cylinder(EYELET_D / 2, 40).moved(Location((x, 0, R + PLATE_T / 2)))
        return rod.rotate(Axis.X, -_m.degrees(_m.asin(max(-0.99, min(0.99, y / R))))).moved(Location((0, 0, -R)))
    holes = []
    n = int((2 * half_l - 2 * corner) // EYELET_PITCH)
    for i in range(n + 1):
        x = -half_l + corner + i * EYELET_PITCH
        for sy in (-1, 1):
            holes.append(eyelet(x, sy * (half_w - MARGIN / 2)))
    m = int((2 * half_w - 2 * corner) // EYELET_PITCH)
    for i in range(m + 1):
        y = -half_w + corner + i * EYELET_PITCH
        for sx in (-1, 1):
            holes.append(eyelet(sx * (half_l - MARGIN / 2), y))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (half_l - corner), sy * (half_w - corner)          # corner-round centre
            r = corner - MARGIN / 2
            holes.append(eyelet(cx + sx * r * _m.cos(_m.radians(45)), cy + sy * r * _m.sin(_m.radians(45))))
    for h in holes:
        p -= h
    return p
