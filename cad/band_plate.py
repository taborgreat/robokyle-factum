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
INSERT_HOLE_D, INSERT_DEPTH = 3.2, 4.2
BOSS_X = IN_L / 2 - 1.0                     # same as the box's ridge screws


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
    # eyelets: radial holes in the margin, along both long sides and both ends
    bbx = foot.bounding_box()
    half_l = bbx.size.X / 2
    n = int((2 * half_l - 10) // EYELET_PITCH)
    for i in range(n + 1):
        x = -half_l + 5 + i * EYELET_PITCH
        for side in ("A", "B"):
            u = bb.ROW_W[side] / 2 + bb.WALL + RIM_CLR + RIM_T + MARGIN / 2
            u = u if side == "B" else -u
            p -= on_row(Cylinder(EYELET_D / 2, 12, align=(Align.CENTER, Align.CENTER, Align.CENTER)), side, x, u, PLATE_T / 2)
    for sx in (-1, 1):
        for y in (-22, -8, 8, 22):
            p -= Cylinder(EYELET_D / 2, 30).moved(Location((sx * (half_l - MARGIN / 2), y, 0)))
    return p
