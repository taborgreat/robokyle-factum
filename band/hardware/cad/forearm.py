"""Forearm ring (build123d): what sits on the 1.5" elastic strap on Kyle's upper forearm.

Frame for every part: X along the arm (+X = wrist end), Y around the arm (along the strap), Z outward.
The skin is a cylinder of radius R_FA about the line y = 0, z = -R_FA.

  electrode_frame   on the skin, holds one dry electrode plate bars-down. A closed elastic loop (<= 22 mm wide) lies
                    across its back, over the plate, and two electrode_bars screw down over the band at the frame's
                    edges: the band is clamped (no creeping), two screws out and the frame lifts off for washing.
                    The electrodes live on their own light band, separate from the module (x2, more later)
  module            on top of the strap, thumb side: both SEN0240 signal boards side by side (each on its own
                    facet of a two-facet tent, like the band box), 2 x PH4 trunk sockets in the elbow wall, the
                    boards' own 3.5 mm jacks through the wrist wall, the BNO08x on the lid underside
  module_lid        tent-shaped cap; press-fit end skirts + 2 x M2x4
  module_backer     curved plate under the strap; 2 x M2x12 from the skin side clamp backer+strap+module

Every cable is plug-to-plug: electrode plate -> 3.5 mm cable -> module; module -> two PH4-PH4 trunk cables -> band.
Strap prep: 2.5 mm holes at the screw positions (hot nail), one 8.5 x 14 notch from the wrist edge per electrode
(the plate's jack lump pokes through it and through the cap).
"""
import math
from build123d import (Box, Cylinder, Location, Align, Axis, Rectangle, RectangleRounded, extrude, fillet, Compound)
from rk_parts import DIM, emg_electrode, emg_signal, imu, jst_socket, _box, _cyl

# ---------------------------------------------------------------- parameters (mm)
R_FA = 34.0          # Kyle's upper-forearm radius (GUESS from the photo: skinny arm, ~21 cm around)
STRAP_T = 1.5        # elastic strap (GUESS)
CLR = 0.3
M2 = DIM["m2"]
HEAD_D, HEAD_H = 4.2, 1.4                      # M2 pan head counterbore (head 3.8 x 1.3)
e, g, JST = DIM["emg_electrode"], DIM["emg_signal"], DIM["jst_ph"]

# electrode frame + cap
LIP = 0.6                                      # under the plate's margins; the bars (1.5) stand 0.9 proud of it
POCKET_D = e["t"] + 0.05                       # plate back flush with the frame back, so the band bears on it
FRAME_T = LIP + POCKET_D
BAND_W = 22.0                                  # the loop band (GUESS: buy 20-22 mm elastic); 1.5 thick
LOOP_X = -5.5                                  # band centred here: its wrist edge stays clear of the plate's jack lump
POCKET_WALL = 1.2
BAR_L, BAR_W, BAR_T = BAND_W + 12.0, 5.0, 2.0  # clamp bar over the band at each edge; screws 6 mm outside the band
BAR_BOSS_D, BAR_BOSS_H = 5.0, 1.3              # the bar sits on two bosses 1.3 tall: the 1.5 band gets squeezed 0.2
BAR_Y = e["w"] / 2 + CLR + POCKET_WALL + BAR_W / 2
BAR_SX = BAND_W / 2 + 3.0                      # screw x offset from the band centre
FR_L, FR_W = 46.0, 2 * (BAR_Y + BAR_W / 2 + 1.0)   # long enough for the clamp bosses (band sits off-centre, toward the elbow)

# module (two-facet tent)
BACKER_T = 2.4
FLOOR_T, WALL, LID_T = 1.6, 1.2, 1.6
IMU_POST = 2.5                                 # IMU on the floor of bay B (header clipped to 2 mm), under board B
IMU_X = -0.5                                   # IMU centre relative to the board centre (between the Gravity pins and the board posts)
STANDOFF = {"A": 2.8, "B": IMU_POST + DIM["imu"]["t"] + DIM["imu"]["comp_h"] + 0.5}   # board B rides over the IMU
RIB = 6.7                                      # between the two board bays: carries the two clamp bosses
ROW_W = g["w"] + 2 * CLR                       # 22.6 per bay
SOCK_D, SOCK_POST, SOCK_SHELF, SOCK_PIN = JST["sock_d"] + 0.2, 1.2, 1.0, 2.0    # pins clipped to 2 mm
SOCK_ZONE = SOCK_D + SOCK_PIN + 3.0            # elbow end of each bay: sockets + pin stubs + wires turning up, before the board
IN_H = STANDOFF["B"] + g["t"] + g["grav_h"] + 0.5                              # lid underside above the floor
SOCK_STACK = 2                                 # the two PH4 trunk sockets stacked in ONE pocket in bay B's elbow wall
                                               # (the two housings get glued into one 2x4 plug: one hole in the wall)
SKIRT, SKIRT_T, SKIRT_CLR = 3.0, 1.0, 0.25
BOSS_D, BOSS_HOLE = 5.5, 2.0
STRAP_W = 38.1                                 # the 1.5" strap; the clamp screws sit OUTSIDE it (no holes in the elastic)
CORNER_R, EDGE_R = 4.0, 1.5

R = R_FA + BACKER_T                            # the module's "arm": the backer's outer face
R_FLOOR = STRAP_T + FLOOR_T                    # floor top above R
W_BOARD = {k: R_FLOOR + v for k, v in STANDOFF.items()}
R_IN = R_FLOOR + IN_H
R_OUT = R_IN + LID_T
PARTING = R_IN - SKIRT
IN_W = 2 * ROW_W + RIB
Y_ROW = {"A": -(RIB / 2 + ROW_W / 2), "B": RIB / 2 + ROW_W / 2}    # A = -Y (flexor board), B = +Y (extensor board)
IN_L = SOCK_ZONE + g["l"] + 2 * CLR
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
X0 = -IN_L / 2
BOSS_X = STRAP_W / 2 + 0.5 + BOSS_D / 2 + 0.3   # clamp bosses just outside the strap, merged into the end walls
X_BOARD = X0 + SOCK_ZONE + CLR + g["l"] / 2      # board centre; Gravity end toward the sockets, jack at +X


# ---------------------------------------------------------------- arm + row frames
def arm_cyl(r, length=400):
    """Cylinder about the arm axis in the MODULE world: z = 0 is the backer's outer face (radius R from the axis)."""
    return Cylinder(r, length).rotate(Axis.Y, 90).moved(Location((0, 0, -R)))


def skin_cyl(r, length=400):
    """Cylinder about the arm axis in the ELECTRODE world: z = 0 is the skin (radius R_FA from the axis)."""
    return Cylinder(r, length).rotate(Axis.Y, 90).moved(Location((0, 0, -R_FA)))


def prism(l, w, z_top, corner=CORNER_R):
    """l x w rounded outline from z = -20 up to z_top (the bottom always ends up inside the arm cylinder)."""
    return extrude(RectangleRounded(l, w, corner), amount=z_top + 20).moved(Location((0, 0, -20)))


def shell(r0, r1, l, w, corner=CORNER_R):
    """Module world: curved plate between skin radii r0 and r1 (from R_FA), clipped to an l x w rounded outline."""
    return (prism(l, w, 20, corner) & arm_cyl(R_FA + r1)) - arm_cyl(R_FA + r0)


def slab(r0, z_top, l, w, corner=CORNER_R):
    """Electrode world: curved underside at skin radius r0, FLAT top at z_top (the flat plate sits on it)."""
    return prism(l, w, z_top, corner) - skin_cyl(R_FA + r0)


def row_angle(k):
    return -math.degrees(math.asin(Y_ROW[k] / R))


def on_row(shape, k, x, u, w, rz=0.0):
    """Place a shape (base on Z=0) in row k's frame at (x, u), base w above R."""
    if rz:
        shape = shape.rotate(Axis.Z, rz)
    shape = shape.moved(Location((x, u, R + w)))
    shape = shape.rotate(Axis.X, row_angle(k))
    return shape.moved(Location((0, 0, -R)))


def row_box(k, x0, x1, u0, u1, w0, w1, r_out=0.0, r_rib=0.0):
    sk = Rectangle(x1 - x0, u1 - u0).moved(Location(((x0 + x1) / 2, (u0 + u1) / 2)))
    outer_sign = -1 if k == "A" else 1
    um = (u0 + u1) / 2
    if r_out:
        sk = fillet([v for v in sk.vertices() if (v.Y - um) * outer_sign > 0], r_out)
    if r_rib:
        sk = fillet([v for v in sk.vertices() if (v.Y - um) * outer_sign < 0], r_rib)
    return on_row(extrude(sk, amount=w1 - w0), k, 0, 0, w0)


def below_plane(k, w, size=400):
    return on_row(Box(size, size, size, align=(Align.CENTER, Align.CENTER, Align.MAX)), k, 0, 0, w)


def tent(wa, wb):
    return below_plane("A", wa) & below_plane("B", wb)


_cache = {}


def outer_form(inset=0.0):
    key = ("outer", inset)
    if key not in _cache:
        halves = None
        for k in ("A", "B"):
            half = ROW_W / 2
            over = half + RIB / 2 + 12.0
            u0, u1 = (-(half + WALL - inset), over) if k == "A" else (-over, half + WALL - inset)
            hb = row_box(k, -OUT_L / 2 + inset, OUT_L / 2 - inset, u0, u1, -40, R_OUT + 20, r_out=CORNER_R - inset)
            halves = hb if halves is None else halves + hb
        form = (halves & tent(R_OUT, R_OUT)) - arm_cyl(R + STRAP_T)
        _cache[key] = form.clean()
    return _cache[key]


def rounded_outer():
    if "rounded" not in _cache:
        o = outer_form()
        try:
            top_z = max(ed.center().Z for ed in o.edges())
            ridge = [ed for ed in o.edges() if abs(ed.center().Z - top_z) < 0.5 and ed.length > OUT_L * 0.8]
            o = fillet(ridge, 3.0)
            tops = [f for f in o.faces() if f.normal_at().Z > 0.3 and f.center().Z > 5]
            sides = [f for f in o.faces() if abs(f.normal_at().Z) < 0.5 and f.center().Z > -30]
            side_edges = [ed for f in sides for ed in f.edges()]
            rim = [ed for f in tops for ed in f.edges() if any(ed.is_same(se) for se in side_edges)]
            o = fillet(rim, EDGE_R)
        except Exception as ex:          # fillets are cosmetic; never let them break the part
            print("fillet skipped:", ex)
            o = outer_form()
        _cache["rounded"] = o
    return _cache["rounded"]


def cavity(k):
    key = ("cav", k)
    if key not in _cache:
        half = ROW_W / 2
        _cache[key] = row_box(k, X0, X0 + IN_L, -half, half, R_FLOOR, R_IN + 30, r_out=1.5, r_rib=1.0)
    return _cache[key]


def cavities():
    return cavity("A") + cavity("B")


def cavity_inset(k, d):
    half = ROW_W / 2 - d
    return row_box(k, X0 + d, X0 + IN_L - d, -half, half, R_FLOOR, R_IN + 30, r_out=1.0, r_rib=0.5)


def end_zone():
    w = OUT_W - 2 * CORNER_R - 2.0
    return (Box(8.0, w, 200).moved(Location((-OUT_L / 2 + 3.0, 0, 0)))
            + Box(8.0, w, 200).moved(Location((OUT_L / 2 - 3.0, 0, 0))))


def skirt_band_cut():
    return ((outer_form() - outer_form(inset=SKIRT_T + SKIRT_CLR)) - tent(PARTING, PARTING)) & end_zone()


# ---------------------------------------------------------------- placements
def placements():
    P = {}
    for k in ("A", "B"):
        P[f"board_{k}"] = on_row(emg_signal(), k, X_BOARD, 0, W_BOARD[k])
        P[f"plug_{k}"] = on_row(_box(g["plug_l"], g["plug_d"], g["plug_d"], g["l"] / 2 + g["plug_l"] / 2 - 6.0, 0,
                                     g["t"] + 5.5 / 2 - g["plug_d"] / 2), k, X_BOARD, 0, W_BOARD[k])
    sk = (jst_socket(4) - _box(10, 20, 10, -JST["sock_d"] - SOCK_PIN - 5, 0, -1)).rotate(Axis.Z, 180)   # pins clipped, opening -X
    for i in range(SOCK_STACK):
        P[f"sock_B{i}"] = on_row(sk, "B", X0, 0, R_FLOOR + SOCK_SHELF + i * JST["sock_t"])
    d = DIM["imu"]
    b = imu() - _box(40, 40, 10, 0, 0, -SOCK_PIN - 10)                                       # header clipped to 2 mm
    P["imu"] = on_row(b, "B", X_BOARD + IMU_X, 0, R_FLOOR + IMU_POST)
    P.update(service_volumes(P))
    return P


def service_volumes(P):
    """Solder, pin stubs and wire bends a real build needs; checked like parts."""
    S = {}
    # behind the stacked trunk sockets: blobs on the 2 mm pin stubs + wires turning up (2.2 mm)
    S["svc_sock_wires"] = on_row(_box(2.2, 8.6, SOCK_STACK * JST["sock_t"], -(JST["sock_d"] + SOCK_PIN) - 1.1, 0, SOCK_SHELF).rotate(Axis.Z, 180),
                                 "B", X0, 0, R_FLOOR)
    # the glued 2x4 trunk plug outside the elbow wall + its cable bend (must clear backer and lid)
    S["svc_trunk_plug"] = on_row(_box(12.0, 9.0, SOCK_STACK * 4.9 + 4.0, WALL + 6.0, 0, SOCK_SHELF - 2.0).rotate(Axis.Z, 180), "B", X0, 0, R_FLOOR)
    # IMU: six wires on its clipped header (-Y edge), under board B
    d = DIM["imu"]
    S["svc_imu_wires"] = on_row(_box(d["l"] - 4, 3.0, 3.5, IMU_X, -d["w"] / 2 - 0.5, IMU_POST - 1.0), "B", X_BOARD, 0, R_FLOOR)
    # each board's Gravity pins (through-hole stubs + wires) under its elbow end
    for k in ("A", "B"):
        S[f"svc_grav_wires_{k}"] = on_row(_box(5.0, 11.0, 2.3, -g["l"] / 2 + 4.0, 0, -2.3), k, X_BOARD, 0, W_BOARD[k])
    # board A's three wires crossing the rib to the sockets, through the rib notch at the elbow end
    S["svc_rib_wires"] = Box(5.0, RIB + 4.0, 3.0).moved(Location((X0 + 8.3, 0, R + R_FLOOR + 4.5)))
    return S


# ---------------------------------------------------------------- module
def sock_pocket_local(n):
    """Block + cut for one straight JST-PH socket lying on its back behind a wall. Local: wall inner face on X=0,
    interior toward -X, floor on Z=0. Open top, back posts, pin slot, plug window."""
    w_ = JST["sock_w"][n]
    top = SOCK_SHELF + JST["sock_t"] + 0.5
    block = _box(SOCK_D + SOCK_POST, w_ + 2 * SOCK_POST, top, -(SOCK_D + SOCK_POST) / 2, 0, 0)
    cut = _box(SOCK_D + 0.5, w_, 30, -SOCK_D / 2 + 0.25, 0, SOCK_SHELF)
    cut += _box(SOCK_POST + 0.4, (n - 1) * JST["pitch"] + 2.4, 30, -SOCK_D - SOCK_POST / 2, 0, SOCK_SHELF)
    cut += _box(WALL + 4, JST["plug_hole_w"][n], JST["plug_hole_h"], WALL / 2, 0,
                SOCK_SHELF + JST["sock_t"] / 2 - JST["plug_hole_h"] / 2)
    return block, cut


def sock_pocket_stack(n, count):
    """Like sock_pocket_local but `count` sockets stacked in one open-top pocket, one tall window."""
    w_ = JST["sock_w"][n]
    top = SOCK_SHELF + count * JST["sock_t"] + 0.5
    block = _box(SOCK_D + SOCK_POST, w_ + 2 * SOCK_POST, top, -(SOCK_D + SOCK_POST) / 2, 0, 0)
    cut = _box(SOCK_D + 0.5, w_, 30, -SOCK_D / 2 + 0.25, 0, SOCK_SHELF)
    cut += _box(SOCK_POST + 0.4, (n - 1) * JST["pitch"] + 2.4, 30, -SOCK_D - SOCK_POST / 2, 0, SOCK_SHELF)
    h_win = (count - 1) * JST["sock_t"] + JST["plug_hole_h"]
    cut += _box(WALL + 4, JST["plug_hole_w"][n], h_win, WALL / 2, 0, SOCK_SHELF + JST["sock_t"] / 2 - JST["plug_hole_h"] / 2)
    return block, cut


def module():
    body = rounded_outer() & tent(R_IN - 0.2, R_IN - 0.2)
    body -= skirt_band_cut()
    body -= cavities()
    # clamp bosses on the ridge (vertical), through 2.0 holes: M2x12 from the backer, M2x4 from the lid
    for sx in (-1, 1):
        body += Cylinder(BOSS_D / 2, 200).moved(Location((sx * BOSS_X, 0, 0))) & outer_form() & tent(R_IN - 0.2, R_IN - 0.2)
        body -= Cylinder(BOSS_HOLE / 2, 200).moved(Location((sx * BOSS_X, 0, 0)))
    body -= skirt_band_cut()
    # the trunk: both PH4 sockets stacked in ONE pocket in bay B's elbow wall (opening faces -X)
    blk, cut = sock_pocket_stack(4, SOCK_STACK)
    body += on_row(blk.rotate(Axis.Z, 180), "B", X0, 0, R_FLOOR) & cavity("B")
    body -= on_row(cut.rotate(Axis.Z, 180), "B", X0, 0, R_FLOOR)
    # rib notch at the elbow end: board A's wires cross to the sockets
    body -= Box(6.0, RIB + 6.0, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((X0 + 8.3, 0, R + R_FLOOR + 4.0)))   # clear of the -X boss
    bl, bw = g["l"], g["w"]
    for k in ("A", "B"):
        so = STANDOFF[k]
        # board: two M2 posts at its mount holes (jack end) + two pads under the Gravity end
        for sy in (-1, 1):
            px, py = X_BOARD + bl / 2 - g["hole_down"], sy * (bw / 2 - g["hole_in"])
            body += on_row(_cyl(BOSS_D - 1.0, so, px, py, 0), k, 0, 0, R_FLOOR)
            body -= on_row(_cyl(BOSS_HOLE, so + 1.2, px, py, -1.2), k, 0, 0, R_FLOOR)            # thread-forming, 1.2 into the floor (0.4 left)
            body += on_row(_box(3.0, 3.0, so, X_BOARD - (bl / 2 - 1.5), sy * (bw / 2 - 1.5), 0), k, 0, 0, R_FLOOR)
        # the board's 3.5 mm jack through the wrist wall (jack body overhangs the board end 1.5 mm into the wall)
        win = extrude(RectangleRounded(5.5 + 1.0, g["jack_w"] + 1.0, 1.0), amount=WALL + 4).rotate(Axis.Y, 90)
        body -= on_row(win, k, X0 + IN_L + WALL / 2 - (WALL + 4) / 2, 0, W_BOARD[k] + g["t"] + 5.5 / 2)
    # IMU under board B: two M2 posts at its +Y-edge corner holes (ASSUMED 2.5 mm in from the corners; if the board
    # has none, glue it) + a pad under the header edge, clear of the clipped pins
    d = DIM["imu"]
    for sx in (-1, 1):
        px, py = X_BOARD + IMU_X + sx * (d["l"] / 2 - 2.5), d["w"] / 2 - 2.5
        body += on_row(_cyl(4.0, IMU_POST, px, py, 0), "B", 0, 0, R_FLOOR)
        body -= on_row(_cyl(BOSS_HOLE, IMU_POST + 1.2, px, py, -1.2), "B", 0, 0, R_FLOOR)
    body += on_row(_box(3.0, 3.0, IMU_POST, X_BOARD + IMU_X, -3.5, 0), "B", 0, 0, R_FLOOR)
    return body


def module_lid():
    cap = rounded_outer() - tent(R_IN, R_IN)
    skirt = ((rounded_outer() - tent(PARTING, PARTING)) & tent(R_IN, R_IN) & end_zone()) - outer_form(inset=SKIRT_T)
    cap += skirt
    for k in ("A", "B"):                                                        # jack windows continue through the skirt
        win = extrude(RectangleRounded(5.5 + 1.0, g["jack_w"] + 1.0, 1.0), amount=WALL + 4).rotate(Axis.Y, 90)
        cap -= on_row(win, k, X0 + IN_L + WALL / 2 - (WALL + 4) / 2, 0, W_BOARD[k] + g["t"] + 5.5 / 2)
    for sx in (-1, 1):
        cap -= Cylinder(M2["clear_d"] / 2, 200).moved(Location((sx * BOSS_X, 0, 0)))
    return cap


def module_backer():
    """Curved plate under the strap. Two rails on its top face box the strap in sideways (they stand 0.2 mm lower
    than the strap, so the module's floor clamps the strap, not the rails)."""
    b = shell(0, BACKER_T, OUT_L, OUT_W)
    for sx in (-1, 1):
        b += shell(BACKER_T, BACKER_T + STRAP_T - 0.2, 2.0, OUT_W - 2.0, corner=0.8).moved(Location((sx * (STRAP_W / 2 + 0.5 + 1.0), 0, 0)))
    for sx in (-1, 1):
        b -= Cylinder(M2["clear_d"] / 2, 200).moved(Location((sx * BOSS_X, 0, 0)))
        b -= Cylinder(HEAD_D / 2, 200, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(Location((sx * BOSS_X, 0, -BACKER_T + HEAD_H)))   # from the skin face
    return b


# ---------------------------------------------------------------- electrode frame + cap
def electrode_placements():
    P = {}
    P["plate"] = emg_electrode().moved(Location((0, 0, LIP)))
    P["plate_plug"] = _box(e["plug_l"], e["plug_d"], e["plug_d"], e["l"] / 2 + e["plug_l"] / 2 - 6.0, 0,
                           LIP + e["t"] + e["jack_h"] / 2 - e["plug_d"] / 2)
    return P


def electrode_frame():
    f = slab(0, FRAME_T, FR_L, FR_W)                                                          # skin face curved, band face flat
    f -= _box(e["l"] + 2 * CLR, e["w"] + 2 * CLR, 30, 0, 0, LIP)                               # plate pocket, open to the band
    span = 2 * e["bar_pitch"] + e["bar_w"]
    f -= _box(span + 1.6, e["bar_l"] + 1.6, 40, 0, 0, -20)                                    # bar window
    f -= _box(9.0, e["jack_w"] + 1.0, 30, e["l"] / 2 + CLR + 3.5, 0, LIP + e["t"] - 0.6)      # jack + plug relief, out to the frame end
    for sy in (-1, 1):
        for sx in (-1, 1):                                                                    # clamp-bar bosses + M2 thread holes
            x, y = LOOP_X + sx * BAR_SX, sy * BAR_Y
            f += _cyl(BAR_BOSS_D, BAR_BOSS_H, x, y, FRAME_T)
            f -= _cyl(M2["thread_form_d"], 6.0, x, y, FRAME_T + BAR_BOSS_H - 6.0 + 0.01)
    return f


def electrode_bar():
    """One clamp bar (two per frame): sits on the bosses, M2x6 at each end, the band runs under it."""
    b = extrude(RectangleRounded(BAR_L, BAR_W, 2.0), amount=BAR_T).moved(Location((LOOP_X, BAR_Y, FRAME_T + BAR_BOSS_H)))
    for sx in (-1, 1):
        b -= _cyl(M2["clear_d"], 10, LOOP_X + sx * BAR_SX, BAR_Y, FRAME_T)
    return b


def electrode_band():
    """The loop band across the frame's back, under both bars (1.5 thick, squeezed to 1.3 under the bars)."""
    return _box(BAND_W, FR_W + 10.0, STRAP_T, LOOP_X, 0, FRAME_T)


# ---------------------------------------------------------------- checks
def _vol(s):
    try:
        return sum(sd.volume for sd in s.solids()) if s is not None else 0.0
    except Exception:
        return 0.0


def summary():
    return (f"module {OUT_L:.1f} x {OUT_W:.1f} (tented, R_FA {R_FA}), ridge {BACKER_T + STRAP_T + R_OUT:.1f} above skin, "
            f"inner {IN_H:.1f}, boards at {STANDOFF['A']}/{STANDOFF['B']}; frame {FR_L:.1f} x {FR_W:.1f} x {FRAME_T:.2f}, "
            f"two clamp bars {BAR_L} x {BAR_W} for a <= {BAND_W:.0f} mm band")


def check():
    bad = 0
    P = placements()
    mod, lid, bk = module(), module_lid(), module_backer()
    THROUGH = {"plug_A", "plug_B", "svc_trunk_plug"}                       # designed to cross a wall
    for pn, piece in (("module", mod), ("lid", lid), ("backer", bk)):
        for k, v in P.items():
            vol = _vol(piece & v)
            if k in THROUGH and pn == "module":
                continue
            if vol >= 0.05: bad += 1
            print(f"{pn:7s} x {k:16s} {vol:8.2f} mm3{'' if vol < 0.05 else '   <-- CLASH'}")
    SKIP = {("svc_sock_wires", "sock_B0"), ("svc_sock_wires", "sock_B1"), ("svc_imu_wires", "imu"),
            ("svc_grav_wires_A", "board_A"), ("svc_grav_wires_B", "board_B"), ("svc_trunk_plug", "sock_B0"), ("svc_trunk_plug", "sock_B1")}
    parts = {k: v for k, v in P.items() if not k.startswith("svc_")}
    for sn, sv in P.items():
        if not sn.startswith("svc_"):
            continue
        for pn, part in parts.items():
            if (sn, pn) in SKIP:
                continue
            vol = _vol(sv & part)
            if vol >= 0.05:
                bad += 1
                print(f"{sn:18s} hits {pn:10s} {vol:8.2f}   <-- CLASH")
    print(f"module & lid overlap: {_vol(mod & lid):.2f}")
    pw = (4 - 1) * 2 + 2.0
    plug = _box(12.0, pw, SOCK_STACK * JST["sock_t"] - 0.1, 0.0, 0, SOCK_SHELF + 0.05).rotate(Axis.Z, 180)   # the glued 2x4 block
    v = _vol(mod & on_row(plug, "B", X0, 0, R_FLOOR))
    if v >= 0.05: bad += 1
    print(f"trunk 2x4 plug through wall: {v:.2f}")
    E = electrode_placements(); E["band"] = electrode_band()
    fr, bar = electrode_frame(), electrode_bar()
    for k, v in E.items():
        vol = _vol(fr & v)
        if vol >= 0.05: bad += 1
        print(f"frame   x {k:10s} {vol:8.2f} mm3{'' if vol < 0.05 else '   <-- CLASH'}")
    for a, b_ in (("band", "plate"), ("band", "plate_plug")):
        vol = _vol(E[a] & E[b_])
        if vol >= 0.05: bad += 1
        print(f"{a:7s} x {b_:10s} {vol:8.2f} mm3{'' if vol < 0.05 else '   <-- CLASH'}")
    print(f"bar     x band       {_vol(bar & E['band']):8.2f} mm3   (the clamp squeeze: 0.2 x band x bar, by design)")
    for k in ("plate", "plate_plug"):
        vol = _vol(bar & E[k])
        if vol >= 0.05: bad += 1
        print(f"bar     x {k:10s} {vol:8.2f} mm3{'' if vol < 0.05 else '   <-- CLASH'}")
    print(f"bar     x frame      {_vol(bar & fr):8.2f} mm3{'' if _vol(bar & fr) < 0.05 else '   <-- CLASH'}")
    if _vol(bar & fr) >= 0.05: bad += 1
    for pn, piece in (("module", mod), ("lid", lid), ("backer", bk), ("frame", fr), ("bar", bar)):
        print(f"{pn}: solids={len(piece.solids())} valid={piece.is_valid} vol={piece.volume:.0f}")
    print(summary())
    print("PASS" if bad == 0 else f"FAIL ({bad})")
    return bad == 0


if __name__ == "__main__":
    check()
