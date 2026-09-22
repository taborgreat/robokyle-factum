# Fit gauge: one flat print that measures this printer's real clearances without calipers.
#
# STEPPED SLOTS (top and bottom edges): each slot is cut for one part and narrows in 4 steps going in.
#   Push the part in square to the plate. The deepest step it enters freely (no force) is the fit:
#   step 1 = +1.2 mm total (loose), 2 = +0.8, 3 = +0.5, 4 = +0.2 (snug). Report the step number per slot.
# HOLE LADDERS (middle rows): round holes in 0.2 mm increments. Report the first hole each part enters.
# SLOT LADDER: rectangular slots for the switch nub and JST-PH plugs.
#
# agentcad run cad/fit_gauge.py --label gauge --export stl
from build123d import Box, Cylinder, Location, Align, Text, extrude, Axis
from rk_parts import DIM

T = 3.0            # plate thickness
STEP_D = 5.0       # depth of each step
STEPS = [1.2, 0.8, 0.5, 0.2]   # total width added at each step, loose -> snug
GAP = 4.0          # wall between stepped slots
HG = 3.0           # wall between ladder holes
LABEL = True

# (label, nominal part width): the part's narrow dimension, pushed in edge-first.
top_slots = [("BATT", DIM["batt"]["w"]), ("STRIP", DIM["strip"]["w"]), ("PICO", DIM["pico"]["w"])]
bot_slots = [("IMU", DIM["imu"]["w"]), ("CHG", DIM["charger"]["w"]), ("SW", DIM["switch"]["w"]),
             ("EMG", DIM["emg_electrode"]["w"])]
# rows of mixed features: a float is a round hole diameter, a tuple is a rectangular slot (x, y)
row_big = [("LED", [5.0, 5.2, 5.4, 5.6]), ("MOT", [10.2, 10.5, 10.8]),
           ("PH2", [(4.3, 5.2), (4.6, 5.4), (4.9, 5.6)])]                       # JST-PH 2-pin housing (4.0 x 4.9)
row_small = [("M2", [1.6, 1.8, 2.0, 2.2]), ("INS", [3.0, 3.2, 3.4]),              # thread-forming / heat-set insert
             ("NUB", [(6.0, 3.0), (7.0, 3.4), (8.0, 3.8)]), ("PH3", [(6.3, 5.2), (6.6, 5.4), (6.9, 5.6)])]
row_cap = [("CAP", [(12.4, 12.4), (12.8, 12.8), (13.2, 13.2)]),                  # 12 mm square button cap
           ("SWB", [(9.2, 4.3), (9.6, 4.7), (10.0, 5.1)])]                        # slide switch body pocket (8.6 x 3.7)

slot_depth = STEP_D * len(STEPS)
def slot_row_w(ss): return sum(w + STEPS[0] + GAP for _, w in ss) + GAP
def fx(f): return f if isinstance(f, float) else f[0]          # x extent of a feature
def fy(f): return f if isinstance(f, float) else f[1]          # y extent
def row_w(rs): return 6 + sum(sum(fx(f) + HG for f in fs) + 4 for _, fs in rs)
plate_l = max(slot_row_w(top_slots), slot_row_w(bot_slots), row_w(row_big), row_w(row_small), row_w(row_cap)) + 2

# row centrelines (y), bottom to top
Y_CAP, Y_SMALL, Y_BIG = slot_depth + 13, slot_depth + 27, slot_depth + 39
plate_w = Y_BIG + 6 + 6 + slot_depth + 4
plate = Box(plate_l, plate_w, T, align=(Align.MIN, Align.MIN, Align.MIN))
labels = []

def cut(shape):
    global plate
    plate -= shape

def stepped_row(ss, y_edge, direction):
    """Cut stepped slots opening at y_edge; direction=-1 cuts down from the top edge, +1 up from the bottom."""
    x = GAP
    for name, w in ss:
        cx = x + (w + STEPS[0]) / 2
        for i, add in enumerate(STEPS):
            depth = STEP_D * (i + 1) + 1
            al = Align.MAX if direction < 0 else Align.MIN
            cut(Box(w + add, depth, T + 2, align=(Align.CENTER, al, Align.MIN)).moved(
                Location((cx, y_edge - direction, -1))))
        labels.append((name, cx - 5, y_edge + direction * (slot_depth + 4)))
        x += w + STEPS[0] + GAP

def feature_row(rs, y):
    x = 6
    for name, fs in rs:
        labels.append((name, x, y + 4 + max(fy(f) for f in fs) / 2))
        for f in fs:
            if isinstance(f, float):
                cut(Cylinder(f / 2, T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x + f / 2, y, -1))))
            else:
                cut(Box(f[0], f[1], T + 2, align=(Align.MIN, Align.CENTER, Align.MIN)).moved(Location((x, y, -1))))
            x += fx(f) + HG
        x += 4

stepped_row(top_slots, plate_w, -1)
stepped_row(bot_slots, 0, +1)
feature_row(row_cap, Y_CAP)
feature_row(row_small, Y_SMALL)
feature_row(row_big, Y_BIG)

if LABEL:   # 0.6 mm raised text
    for name, lx, ly in labels:
        plate += extrude(Text(name, font_size=3.5, align=(Align.MIN, Align.CENTER)), amount=0.6).moved(
            Location((lx, ly, T)))

# orientation mark: chamfered corner at the origin so the label side is unambiguous
cut(Box(6, 6, T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(Axis.Z, 45).moved(Location((0, 0, -1))))

show_object(plate, id="fit_gauge", name="fit gauge")
