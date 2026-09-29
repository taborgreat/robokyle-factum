# Run after any change to a lid, wall or boss: every screw hole, insert seat and counterbore must report OK.
# .venv/Scripts/python band/hardware/cad/check_fasteners.py
"""Every screw hole / insert seat in all printed parts: is the mouth open, is the bore clear to the intended depth?
A small sphere straddling the surface at the hole axis must be AIR (mouth open); spheres down the axis must be AIR
(bore clear); a ring of spheres around the mouth must be SOLID (there is a wall to hold the screw/insert)."""
import math, band_box as bb, band_plate as bp, forearm as fa
from build123d import *
def solid_of(part): return max(part.solids(), key=lambda s: abs(s.volume))
def hit(sol, sph): return abs((sol & sph).volume) > 1e-7
def probe_axis(name, sol, place, depths, ring_r):
    """place(u, v, w) -> sphere placed in the hole's own frame: (u, v) across, w along the axis (0 = mouth, + into)."""
    mouth = hit(sol, place(0, 0, 0.0))
    bore = [hit(sol, place(0, 0, d)) for d in depths]
    ring = [hit(sol, place(ring_r * math.cos(a), ring_r * math.sin(a), depths[-1] * 0.6)) for a in (0, 1.57, 3.14, 4.71)]
    ok = (not mouth) and (not any(bore)) and all(ring)
    print(("  OK  " if ok else "  BAD ") + name, "| mouth", "solid!" if mouth else "open", "| bore", "".join("X" if b else "." for b in bore),
          "| ring", "".join("#" if r else "." for r in ring))
    return ok
S = 0.25
bad = 0
# ---------------- band box
box = solid_of(bb.box())
def row_place(k, x, u, w_top, sign=-1):
    return lambda du, dv, d: bb.on_row(Sphere(S).moved(Location((x + du, u + dv, 0))), k, 0, 0, w_top + sign * d)
xl = -(bb.IN_L / 2 - 3.5); xr = bb.IN_L / 2 - 3.5
print("BAND BOX")
bad += not probe_axis("-X lid insert (row B frame, tilted)", box, row_place("B", xl, bb.rib_screw_u(), bb.R_IN["B"]), (0.6, 2.0, 4.2), 1.7 + 0.5)
bad += not probe_axis("+X lid insert (row B frame)", box, row_place("B", xr, bb.CHEST_BOSS_U, bb.R_IN["B"]), (0.6, 2.0, 4.2), 1.7 + 0.5)
x_strip = bb.X0 + bb.STRIP_X0 + bb.s["l"] / 2
for sx in (-1, 1):
    for sy in (-1, 1):
        nm = "strip standoff %s%s (M2 thread)" % ("-X" if sx < 0 else "+X", " rib" if sy < 0 else " chest")
        bad += not probe_axis(nm, box, row_place("B", x_strip + sx * bb.s["standoff_x"], sy * bb.s["standoff_u"], bb.R_FLOOR + bb.STANDOFF), (0.5, 1.5, 2.6), 1.0 + 0.5)
for sx in (-1, 1):
    x = sx * (bb.IN_L / 2 - 3.5)
    top = bb.R_FLOOR + bb.PLATE_POST_UP + bb.POST_GAP + bb.POST_FLANGE_T
    pl = lambda du, dv, d, x=x, top=top: Sphere(S).moved(Location((x + du, bb.Y_POST + dv, top - d)))
    bad += not probe_axis("plate screw %s: web bore (4.5) + 2.3 through" % ("-X" if sx < 0 else "+X"), box, pl, (0.4, 1.0, 1.4), 2.25 + 0.6)
    plb = lambda du, dv, d, x=x: Sphere(S).moved(Location((x + du, bb.Y_POST + dv, bb.PLATE_T + 0.2 + d)))   # post pocket from below
    bad += not probe_axis("plate post pocket %s (from below)" % ("-X" if sx < 0 else "+X"), box, plb, (0.5, 1.5, 2.6), 3.1 + 0.6)
lid = solid_of(bb.lid())
print("BAND LID")
for nm, x, u in (("-X screw clearance", xl, bb.rib_screw_u()), ("+X screw clearance", xr, bb.CHEST_BOSS_U)):
    bad += not probe_axis(nm, lid, row_place("B", x, u, bb.R_IN["B"] + bb.LID_T + 0.5), (0.7, 1.3, 2.2), 1.15 + 0.5)
plate = solid_of(bp.plate() if hasattr(bp, "plate") else bp.build())
print("BAND PLATE")
for sx in (-1, 1):
    x = sx * (bb.IN_L / 2 - 3.5)
    top = bb.R_FLOOR + bb.PLATE_POST_UP - (bb.PLATE_T + 0.2) + bb.PLATE_T + 0.2
    pl = lambda du, dv, d, x=x, top=top: Sphere(S).moved(Location((x + du, bb.Y_POST + dv, top - d)))
    bad += not probe_axis("post insert %s (3.4 x 4.6 from the post top)" % ("-X" if sx < 0 else "+X"), plate, pl, (0.6, 2.0, 4.2), 1.7 + 0.5)
# ---------------- forearm
mod, mlid, bk, fr = solid_of(fa.module()), solid_of(fa.module_lid()), solid_of(fa.module_backer()), solid_of(fa.electrode_frame())
print("FOREARM MODULE")
for sx in (-1, 1):
    x = sx * fa.BOSS_X
    top = fa.crest_z(fa.R_IN - fa.BOSS_SHORT)
    pl = lambda du, dv, d, x=x, top=top: Sphere(S).moved(Location((x + du, dv, top - d)))
    bad += not probe_axis("crest boss %s: lid insert 3.4 x 4.6 + bore, from the top" % ("-X" if sx < 0 else "+X"), mod, pl, (0.6, 2.0, 4.2, 5.5, 6.3), 1.7 + 0.5)
    plb = lambda du, dv, d, x=x: Sphere(S).moved(Location((x + du, dv, fa.STRAP_T + d)))
    bad += not probe_axis("crest boss %s: clamp insert 3.4 x 4.6 + bore, from the strap face" % ("-X" if sx < 0 else "+X"), mod, plb, (0.6, 2.0, 4.2, 5.5, 6.3), 1.7 + 0.5)
    plm = lambda du, dv, d, x=x: Sphere(S).moved(Location((x + du, dv, fa.STRAP_T + 6.6 + 1.0 + d)))
    bad += not (hit(mod, plm(0, 0, 0)) and hit(mod, plm(0, 0, 3.0)))          # solid between the two pockets
    print(("  OK  " if hit(mod, plm(0, 0, 0)) and hit(mod, plm(0, 0, 3.0)) else "  BAD ") + "crest boss %s: solid core between the pockets" % ("-X" if sx < 0 else "+X"))
for k, sg in (("A", -1), ("B", 1)):
    pl = lambda du, dv, d, k=k, sg=sg: fa.on_row(Sphere(S).moved(Location((du, sg * fa.EAR_U + dv, 0))), k, 0, 0, fa.R_IN - fa.BOSS_SHORT - d)
    bad += not probe_axis("side ear %s: lid insert 3.4 x 4.6 + bore (row frame)" % k, mod, pl, (0.6, 2.0, 4.2, 5.5, 6.3), 1.7 + 0.5)
g = fa.g
for k in "AB":
    so = fa.STANDOFF[k]
    for sy in (-1, 1):
        px, py = fa.X_BOARD + g["l"] / 2 - g["hole_down"], sy * (g["w"] / 2 - g["hole_in"])
        pl = lambda du, dv, d, px=px, py=py, so=so, k=k: fa.on_row(Sphere(S).moved(Location((px + du, py + dv, 0))), k, 0, 0, fa.R_FLOOR + so - d)
        bad += not probe_axis("board %s post %s (M3 thread 2.6)" % (k, "+" if sy > 0 else "-"), mod, pl, (0.9, 2.0, so + 0.8), 1.3 + 0.6)
d = fa.DIM["imu"]
for sx in (-1, 1):
    px, py = fa.X_BOARD + fa.IMU_X + sx * (d["l"] / 2 - 2.5), d["w"] / 2 - 2.5
    pl = lambda du, dv, d_, px=px, py=py: fa.on_row(Sphere(S).moved(Location((px + du, py + dv, 0))), "B", 0, 0, fa.R_FLOOR + fa.IMU_POST - d_)
    bad += not probe_axis("IMU post %s (M2 thread)" % ("-X" if sx < 0 else "+X"), mod, pl, (0.5, 1.5, fa.IMU_POST + 0.8), 1.0 + 0.6)
print("FOREARM LID")
for sx in (-1, 1):
    x = sx * fa.BOSS_X
    pl = lambda du, dv, d, x=x: Sphere(S).moved(Location((x + du, dv, fa.crest_z(fa.R_OUT) + 0.4 - d)))
    bad += not probe_axis("crest screw clearance %s" % ("-X" if sx < 0 else "+X"), mlid, pl, (0.8, 1.6, 2.0), 1.15 + 0.6)
for k, sg in (("A", -1), ("B", 1)):
    pl = lambda du, dv, d, k=k, sg=sg: fa.on_row(Sphere(S).moved(Location((du, sg * fa.EAR_U + dv, 0))), k, 0, 0, fa.R_OUT + 0.4 - d)
    bad += not probe_axis("ear screw clearance %s (row frame)" % k, mlid, pl, (0.8, 1.6, 2.0), 1.15 + 0.6)
print("FOREARM BACKER")
for sx in (-1, 1):
    x = sx * fa.BOSS_X
    pl = lambda du, dv, d, x=x: Sphere(S).moved(Location((x + du, dv, -fa.BACKER_T + 0.0 + d)))     # skin face at z = -BACKER_T? probe from there
    bad += not probe_axis("clamp counterbore %s (4.2 x 1.4 from the skin face)" % ("-X" if sx < 0 else "+X"), bk, pl, (0.3, 0.9, 1.2), 2.1 + 0.6)
print("ELECTRODE FRAME")
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = fa.LOOP_X + sx * fa.BAR_SX, sy * fa.BAR_Y
        pl = lambda du, dv, d, x=x, y=y: Sphere(S).moved(Location((x + du, y + dv, fa.FRAME_T + fa.BAR_BOSS_H - d)))
        bad += not probe_axis("cover boss (%s,%s) (M2 thread)" % ("+" if sx > 0 else "-", "+" if sy > 0 else "-"), fr, pl, (0.5, 2.0, 4.5), 1.0 + 0.6)
print("BAD:", bad)
