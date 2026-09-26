"""EMG band upper-arm cuff box, v5 (build123d). Layout module; run through band_box_run.py, check with check_box.py.

Frame: X along the arm (+X = elbow end, cable exit), Y around the arm (+Y = chest/anterior, -Y = triceps),
Z radial at y=0. The arm axis is the line y=0, z=-R.

Two rows: A (battery, charger, Qi) on the -Y side, B (Pico strip with the button) on the +Y side. Each row is
built in its own frame: the plane tangent to the arm at the row's centre Y_k. In a row frame (x, u, w): u runs
across the arm, w is height above the ARM SURFACE (so the floor is at w = R_FLOOR). Bay walls are perpendicular
to the row's lid facet, so tilted parts never lean into a vertical wall. The two facets meet at a rounded ridge.
The lid's skirt wraps over a thinned wall top; two M2 screws on the ridge line go lid -> box -> plate inserts.
"""
import math
from build123d import (Box, Cylinder, Location, Align, Axis, Rectangle, RectangleRounded, extrude, fillet, Compound)
from rk_parts import (DIM, pico_on_strip, pico_usb_plug, usb_wall_cut, battery, charger, charger_keepout, slide_switch,
                      tactile_button, tactile_button_keepout, led_5mm, ws2812_segment, coin_motor, qi_coil, qi_board,
                      jst_socket, _box)

# ---------------------------------------------------------------- parameters (mm)
R = 44.0            # upper-arm radius at the cuff (GUESS: measure Kyle's arm circumference / 2pi)
CLR = 0.5           # per-side pocket clearance for rigid parts: gauge 2026-09-22 -> slots print ~0.4 undersize
BATT_CLR = 0.7      # pouch cells swell; foam takes up the rest
PLATE_T = 2.0       # sewn plate under the box
FLOOR_T = 1.6
R_FLOOR = PLATE_T + FLOOR_T
WALL = 2.0
LID_T = 1.6
RIB = 3.0           # floor-level gap between the two bays (walls diverge going up)
FOAM_T = 1.5
STANDOFF = 2.0      # strip standoffs (solder stubs hang 1.5)
CORNER_R = 7.0
RIDGE_R = 6.0
EDGE_R = 2.5
SKIRT, SKIRT_T, SKIRT_CLR = 4.0, 1.0, 0.25    # lid skirt height / thickness / clearance over the thinned wall (PETG lap)
SCREW_D = 2.3                                 # M2 clearance (lid)
LID_BOSS_D, LID_BOSS_HOLE = 6.4, DIM["m2"]["insert_hole_d"]   # full-round bosses with M2 heat-set inserts; M2x6 from the lid
M2_FORM_D = DIM["m2"]["thread_form_d"]
M2 = DIM["m2"]
PLATE_POST_D, PLATE_POST_UP = 6.2, 2.9        # the plate's posts rise this far above the floor, INTO a floor boss
POST_FLANGE_T, POST_GAP = 1.5, 0.2            # the boss's top web the M2x6 pulls down onto the post's insert
POST_BOSS_D, POST_BORE_D = 9.0, 4.5           # boss around the post; driver/head bore above the flange
SERVICE_A = 0.4     # air above the coil
LED_PROUD = 1.2     # LED dome tip above the lid (Tabor: ~1 mm is fine); keeps the lid boss above the Pico edge

b, s, c, q = DIM["batt"], DIM["strip"], DIM["charger"], DIM["qi"]
SW_D, LED_D, WS_D = DIM["switch"], DIM["led"], DIM["ws2812"]
LED_X, LED_Y = 25.4, 6.35      # LED SOLDERED INTO the strip: legs in rows 21-22, chest side, 3rd column in (strip coords)
                               # (columns 1/10 of rows 21-22 are next to the standoff screws at row 21)
LED_STANDOFF = 1.0             # flange sits this far above the strip (leg shoulder)
                               # (print 2026-09-24: the old lid-mounted LED's legs reached the Pico - now it is a strip part)
N_PIX = 3                      # WS2812 pixels on the crest (4 would run into the ridge screws)
BTN_ZONE = 0.0                 # (kept for the summary: the button lives in the forearm module now)
BAR_GAP = 2.2                  # air between the bar's top (the LEDs) and the lid's inner ridge apex
SLIT_L, SLIT_W, SLIT_T = 8.0, 3.0, 0.8   # one thinned slit-window per pixel; SLIT_T = plastic left over the LED
SW_X, SW_W = 8.0, 11.0         # switch along the chest wall; body bottom height above the arm
SW_INSET = 1.0                 # nub base this far inside the wall's inner face
CHG_U = -4.0                   # charger shifted toward the triceps wall: battery plug clears the rib and the -X plate post
COIL_U = 2.0                   # coil shifted toward the rib (it is wider than the battery bay)
# (2026-09-24 print review: the button and the coin motor moved to the forearm module - the button is reachable
#  there and the motor sits against the strap. Both ride the trunk, which is now a PH6 + a PH4.)
# wall sockets (straight JST-PH headers lying on their backs in pockets behind the +X end wall; plug window = the
# gauge's plug slot, so the wall is the flange; a dab of hot glue keeps them from lifting)
JST = DIM["jst_ph"]
SOCK_D, SOCK_POST, SOCK_SHELF = JST["sock_d"] + 0.2, 1.2, 1.0    # pocket depth, back-post thickness, shelf above the floor
SOCK_PIN = 2.0                 # socket pins clipped to 2 mm (the trunk pins would otherwise reach the battery ring)
SOCK_ZONE = 3.0                # extra bay length at the +X end so the socket pins clear the battery ring
TRUNK_A = [(6, -3.65)]                   # row A end wall: trunk plug A, PH6 (3V3 GND EMG1 EMG2 BTN MOTOR)
ROW_B_SOCKETS = [(4, -8.9), (3, 2.7)]    # row B end wall: trunk plug B, PH4 (SDA SCL INT RST) + hand cord PH3 (TX RX GND)
SOCK_END_ZONE = 12.0                     # bay length past the strip for those pockets: 7.4 pocket + 2 pins + wires
NOTCH_W = 17.0                 # middle-wall notches: wider than the wall's leaning faces at the top (13.3), no fins left
# (2026-09-24: nothing is mounted on the lid any more - the LED stands on the strip, the light bar lies in the
#  middle wall's pocket and the lid closes over it - so there is no lid pigtail and no strip socket for it)

# ---------------------------------------------------------------- row geometry
ROW_W = {"A": b["w"] + 2 * BATT_CLR, "B": s["w"] + 2 * CLR}
IN_W = ROW_W["A"] + RIB + ROW_W["B"]
Y_ROW = {"A": -IN_W / 2 + ROW_W["A"] / 2, "B": IN_W / 2 - ROW_W["B"] / 2}
LEAD_GAP = 4.0
BATT_LIP = 2.0                 # the cell's tape lip (3.7, soft) at the lead end: the ring pocket is this much longer there (2.0 = all the room before the charger)
SOCK_ZONE_A = SOCK_D + SOCK_PIN + 1.0       # row A: trunk pocket + pin stubs + wire bend past the battery ring
USB_NOSE = DIM["usb_plug"]["nose_in"]                        # the Pico's USB socket pokes this far into the wall hole
USB_FACE_REL = (s["pico_row_offset"] - DIM["pico"]["l"] / 2 - DIM["pico"]["usb_overhang"]) + s["l"] / 2   # USB face vs strip end (- = past it)
STRIP_X0 = -USB_NOSE - USB_FACE_REL                            # strip's -X end relative to the wall's inner face
ROW_L = {"A": CLR + c["w"] + CLR + LEAD_GAP + b["l"] + CLR + 5.0 + 1.6 + SOCK_ZONE_A,    # + the two 2.5 shifts, ring wall, sockets
         "B": STRIP_X0 + s["l"] + CLR + SOCK_END_ZONE}
IN_L = max(ROW_L.values())
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
X0 = -IN_L / 2

# radial stack (heights above the arm surface)
W_BATT = R_FLOOR + FOAM_T
W_STRIP = R_FLOOR + STANDOFF
TOP_A = W_BATT + b["h"] + q["ferrite_t"] + q["coil_t"]
USB_TOP = W_STRIP + s["t"] + DIM["pico"]["hdr_base"] + DIM["pico"]["t"] + DIM["pico"]["usb_h"] / 2 + DIM["usb_plug"]["h"] / 2
R_IN = {"A": TOP_A + SERVICE_A, "B": USB_TOP + 0.3}         # lid underside per row: the USB plug sets row B
R_OUT = {k: v + LID_T for k, v in R_IN.items()}
PARTING = {k: v - SKIRT for k, v in R_IN.items()}
SW_U = ROW_W["B"] / 2 - SW_INSET
NOTCH_D = SW_D["nub_h"] - SW_INSET - WALL + 0.6      # finger recess depth (nub tip 0.6 below the surface)
Y_RIB = (Y_ROW["A"] + ROW_W["A"] / 2 + Y_ROW["B"] - ROW_W["B"] / 2) / 2      # global y of the rib centre at floor
Y_BOSS = Y_RIB + 4.5      # -X lid boss, strip side of the middle wall (snip the strip's -X rib-side corner ~8 mm)
CHEST_BOSS_U = ROW_W["B"] / 2 - 1.85   # +X lid boss: row B's chest corner (the rib corner holds the cord socket)
Y_POST = Y_RIB - 3.5      # plate posts, battery side of the middle wall (driver path clear of the charger wires)


# ---------------------------------------------------------------- frames
def row_angle(k):
    return -math.degrees(math.asin(Y_ROW[k] / R))


def on_row(shape, k, x, u, w, rz=0.0):
    """Place a part (base on Z=0) into row k's frame at (x, u) with its base at height w above the arm."""
    if rz:
        shape = shape.rotate(Axis.Z, rz)
    shape = shape.moved(Location((x, u, R + w)))
    shape = shape.rotate(Axis.X, row_angle(k))
    return shape.moved(Location((0, 0, -R)))


def row_box(k, x0, x1, u0, u1, w0, w1, r_out=0.0, r_rib=0.0):
    """Box in row k's frame. r_out rounds the two corners on the row's outer side, r_rib the rib side."""
    sk = Rectangle(x1 - x0, u1 - u0).moved(Location(((x0 + x1) / 2, (u0 + u1) / 2)))
    outer_sign = -1 if k == "A" else 1
    um = (u0 + u1) / 2
    if r_out:
        sk = fillet([v for v in sk.vertices() if (v.Y - um) * outer_sign > 0], r_out)
    if r_rib:
        sk = fillet([v for v in sk.vertices() if (v.Y - um) * outer_sign < 0], r_rib)
    solid = extrude(sk, amount=w1 - w0)
    return on_row(solid, k, 0, 0, w0)


def below_plane(k, w, size=400):
    return on_row(Box(size, size, size, align=(Align.CENTER, Align.CENTER, Align.MAX)), k, 0, 0, w)


def tent(wa, wb):
    return below_plane("A", wa) & below_plane("B", wb)


def arm_cyl(dr, length=400):
    return Cylinder(R + dr, length).rotate(Axis.Y, 90).moved(Location((0, 0, -R)))


def outer_sides(k, inset=0.0):
    """(u0, u1) of row k's outer form: outer wall at ROW_W/2 + WALL - inset, overlapping past the rib."""
    half = ROW_W[k] / 2
    over = half + RIB / 2 + 16.0
    return (-(half + WALL - inset), over) if k == "A" else (-over, half + WALL - inset)


# ---------------------------------------------------------------- outer form
_cache = {}


def outer_form(inset=0.0, arm_cut=True):
    """Union of both rows' outer boxes, under the tent. inset shrinks ends and outer sides (negative grows them).
    arm_cut=False keeps the solid going down through the arm (footprint for the plate)."""
    key = ("outer", inset, arm_cut)
    if key not in _cache:
        halves = None
        for k in ("A", "B"):
            u0, u1 = outer_sides(k, inset)
            hb = row_box(k, -OUT_L / 2 + inset, OUT_L / 2 - inset, u0, u1, -60, R_OUT[k] + 20, r_out=CORNER_R - inset)
            halves = hb if halves is None else halves + hb
        form = halves & tent(R_OUT["A"], R_OUT["B"])
        if arm_cut:
            form -= arm_cyl(PLATE_T)
        _cache[key] = form.clean()
    return _cache[key]


def rounded_outer():
    if "rounded" not in _cache:
        o = outer_form()
        top_z = max(e.center().Z for e in o.edges())
        ridge = [e for e in o.edges() if abs(e.center().Z - top_z) < 0.5 and e.length > OUT_L * 0.8]
        o = fillet(ridge, RIDGE_R)
        tops = [f for f in o.faces() if f.normal_at().Z > 0.3 and f.center().Z > 5]
        sides = [f for f in o.faces() if abs(f.normal_at().Z) < 0.5 and f.center().Z > -30]
        side_edges = [e for f in sides for e in f.edges()]
        rim = [e for f in tops for e in f.edges() if any(e.is_same(se) for se in side_edges)]
        _cache["rounded"] = fillet(rim, EDGE_R)
    return _cache["rounded"]


def cavity(k):
    key = ("cav", k)
    if key not in _cache:
        half = ROW_W[k] / 2
        _cache[key] = row_box(k, X0, X0 + IN_L, -half, half, R_FLOOR, R_IN[k] + 30, r_out=2.5, r_rib=1.0)   # parts have sharp corners
    return _cache[key]


def cavity_inset(k, d):
    """Bay k shrunk by d on every side: for lid features that hang into the bay and must not rub the walls."""
    half = ROW_W[k] / 2 - d
    return row_box(k, X0 + d, X0 + IN_L - d, -half, half, R_FLOOR, R_IN[k] + 30, r_out=max(2.5 - d, 0.5), r_rib=0.5)


def cavities():
    return cavity("A") + cavity("B")


def parting_solid():
    return tent(PARTING["A"], PARTING["B"])


def end_zone():
    """Where the lid's skirt lives: the flat middle of each vertical end wall. The long sides lean outward, so a
    skirt there would wedge when the lid lifts; those sides are a plain butt joint on the tent."""
    w = OUT_W - 2 * CORNER_R - 2.0
    return (Box(8.0, w, 200).moved(Location((-OUT_L / 2 + 3.0, 0, 0)))
            + Box(8.0, w, 200).moved(Location((OUT_L / 2 - 3.0, 0, 0))))


def skirt_band_cut():
    """The box's wall is thinned above the parting line only in the end zones."""
    return ((outer_form() - outer_form(inset=SKIRT_T + SKIRT_CLR)) - parting_solid()) & end_zone()


def ridge(wa, wb, n=2000):
    """Global (y, z) where the two facet planes (heights wa, wb in their row frames) meet."""
    import math as _m
    def plane_pts(k, w):
        a = _m.radians(row_angle(k)); pts = []
        for i in range(n + 1):
            u = -60 + 120 * i / n
            y = u * _m.cos(a) - (R + w) * _m.sin(a); z = u * _m.sin(a) + (R + w) * _m.cos(a) - R
            pts.append((y, z))
        return pts
    A, B = plane_pts("A", wa), plane_pts("B", wb)
    def z_at(pts, y):
        for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
            if y0 <= y <= y1 or y1 <= y <= y0:
                return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
        return None
    best = None
    for i in range(n + 1):
        y = -30 + 60 * i / n
        za, zb = z_at(A, y), z_at(B, y)
        if za is None or zb is None: continue
        d = abs(za - zb)
        if best is None or d < best[0]: best = (d, y, min(za, zb))
    return best[1], best[2]


def tent_z(y, wa, wb, n=2000):
    """Height (global z) of the tent surface (min of the two facet planes) at global y."""
    import math as _m
    def z_of(k, w):
        a = _m.radians(row_angle(k))
        for i in range(n):
            u0 = -60 + 120 * i / n; u1 = u0 + 120 / n
            y0 = u0 * _m.cos(a) - (R + w) * _m.sin(a); y1 = u1 * _m.cos(a) - (R + w) * _m.sin(a)
            if min(y0, y1) <= y <= max(y0, y1):
                z0 = u0 * _m.sin(a) + (R + w) * _m.cos(a) - R; z1 = u1 * _m.sin(a) + (R + w) * _m.cos(a) - R
                return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
        return None
    return min(z_of("A", wa), z_of("B", wb))


def bar_pose():
    """Global position of the WS2812 bar: centred on the crest, top BAR_GAP below the inner ridge apex."""
    y_r, z_in = ridge(R_IN["A"], R_IN["B"])
    z_bottom = z_in - BAR_GAP - WS_D["t"] - WS_D["led_h"]
    return y_r, z_in, z_bottom


# ---------------------------------------------------------------- part placement
def placements():
    P = {}
    xa = X0 + CLR
    x_chg = xa + c["w"] / 2 + 2.5          # off the end wall, out of the bay's corner round
    x_batt = xa + c["w"] + CLR + LEAD_GAP + b["l"] / 2 + 2.5
    P["charger"] = on_row(charger(), "A", x_chg, CHG_U, R_FLOOR, rz=-90)          # crosswise; socket toward the rib (+u)
    P["charger_keepout"] = on_row(charger_keepout(), "A", x_chg, CHG_U, R_FLOOR, rz=-90)
    P["battery"] = on_row(battery(), "A", x_batt, 0, W_BATT)
    # Qi board lies flat on top of the charger (Kapton between): nothing on the lid needs the coil's wires any more
    P["qi_board"] = on_row(qi_board(), "A", xa + 7.4, -1.5, R_FLOOR + c["h"] + 2.3, rz=90)   # above the charger's wires
    P["qi_coil"] = on_row(qi_coil(), "A", x_batt, COIL_U, R_IN["A"] - q["coil_t"] - q["ferrite_t"])
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    # the strip as built: its USB-end rib-side corner is snipped ~8 mm (the lid boss stands there)
    strip_part = pico_on_strip() - _box(9.0, 9.0, 10, -s["l"] / 2 + 2.5, -s["w"] / 2 + 2.5, -3)
    strip_part -= _box(4.0, 4.0, 10, 0, 0, -3).rotate(Axis.Z, 45).moved(Location((-s["l"] / 2, s["w"] / 2, 0)))   # USB-end chest corner nipped ~2.8 mm at 45 deg (bay corner round)
    P["strip"] = on_row(strip_part, "B", x_strip, 0, W_STRIP)
    x_pico = x_strip + s["pico_row_offset"]
    P["usb_plug"] = on_row(pico_usb_plug(), "B", x_pico, 0, W_STRIP + s["t"] + DIM["pico"]["hdr_base"])
    P["led"] = on_row(led_5mm(leg_l=LED_STANDOFF + s["t"] + 1.5), "B", x_strip + LED_X, LED_Y, W_STRIP + s["t"] + LED_STANDOFF)   # on the strip, legs clipped 1.5 below it
    y_r, _, z_b = bar_pose()
    P["ws2812"] = ws2812_segment(N_PIX).moved(Location((0, y_r, z_b - 0.6)))    # lying on its pocket floor in the middle wall
    # switch: nub toward +u through the chest wall; origin at the nub base; body 1 mm inside the wall so the
    # nub tip is flush with the outer surface (and 0.6 recessed inside the finger notch)
    sw = slide_switch().rotate(Axis.X, -90).moved(Location((0, -SW_D["h"], 0)))
    P["switch"] = on_row(sw, "B", x_strip + SW_X, SW_U, SW_W + SW_D["w"] / 2)
    for k, bank in (("A", TRUNK_A), ("B", ROW_B_SOCKETS)):
        for i, (n, u) in enumerate(bank):
            sk = jst_socket(n) - _box(10, 20, 10, -JST["sock_d"] - SOCK_PIN - 5, 0, -1)       # pins clipped
            P[f"sock_{k}{i}"] = on_row(sk, k, X0 + IN_L, u, R_FLOOR + SOCK_SHELF)
    for sx in (-1, 1):                                                      # the plate's posts, as the box sees them
        x = sx * (IN_L / 2 - 3.5)
        P[f"plate_post_{'L' if sx < 0 else 'R'}"] = Cylinder(PLATE_POST_D / 2, R_FLOOR + PLATE_POST_UP - (PLATE_T + 0.2),
            align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, Y_POST, PLATE_T + 0.2)))   # the part inside the box
    P.update(service_volumes(P))
    return P


def service_volumes(P):
    """Wire bends, solder blobs and pin stubs: volumes a real build needs around the parts. Checked like parts
    (check_box.py) so 'it fits on screen' includes the soldering. Sizes are what a careful hand build needs, not
    generous - if one of these clashes, the layout is wrong, not the zone."""
    S = {}
    xa = X0 + CLR
    x_chg = xa + c["w"] / 2 + 2.5
    x_batt = xa + c["w"] + CLR + LEAD_GAP + b["l"] / 2 + 2.5
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    # charger: wires soldered flat onto its pads (blob + wire = 2 mm); the Qi board sits on Kapton above that
    S["svc_charger_solder"] = on_row(_box(c["l"], c["w"], 2.0, 0, 0, c["h"]), "A", x_chg, CHG_U, R_FLOOR, rz=-90)
    # battery tape lip + leads folding out of the cell's -X end through the ring's lead notch (3 mm, then they turn
    # toward the charger's socket on the rib side)
    S["svc_batt_leads"] = on_row(_box(3.0, 7.0, 6.0, -(b["l"] / 2 + 1.5), 0, 0), "A", x_batt, 0, R_FLOOR)
    # wall sockets: solder blob + wire turning up, 2.2 mm beyond the clipped pin tips
    for k, bank in (("A", TRUNK_A), ("B", ROW_B_SOCKETS)):
        for i, (n, u) in enumerate(bank):
            z = _box(2.2, (n - 1) * JST["pitch"] + 2.6, 4.0, -(JST["sock_d"] + SOCK_PIN) - 1.1, 0, SOCK_SHELF + JST["sock_t"] / 2 - 2.0)
            S[f"svc_sock_{k}{i}"] = on_row(z, k, X0 + IN_L, u, R_FLOOR)
    # strip: tall parts (transistor, diodes, resistors on end) up to 4.5 mm on the two outer rows beside the Pico.
    # Rib side: from 20 mm before the strip centre (the -X corner is snipped for the lid boss) to the free rows.
    # Chest side: same, minus the switch's and the LED's shadows - keep those spots for low parts.
    S["svc_strip_margin_rib"] = on_row(_box(43.0, 4.0, 4.5, 1.5, -12.7, s["t"]), "B", x_strip, 0, W_STRIP)
    chest = _box(43.0, 4.0, 4.5, 1.5, 12.7, s["t"])
    chest -= _box(SW_D["l"] + 3.0, 6.0, 6.0, SW_X, 12.7, s["t"] - 0.5)
    chest -= _box(8.0, 6.0, 6.0, LED_X, 12.7, s["t"] - 0.5)                            # the +X standoff screw head is here
    S["svc_strip_margin_chest"] = on_row(chest, "B", x_strip, 0, W_STRIP)
    # LED: 470 R + its two solder joints on the strip beside it (chest column, rows 19-20)
    S["svc_led_solder"] = on_row(_box(2.6, 5.0, 2.5, LED_X, LED_Y - 5.7, s["t"]), "B", x_strip, 0, W_STRIP)   # 470 R lying flat beside the LED, toward the centre line
    # plate screws: head + driver above each post boss (M2 head 3.8, driver shaft 4)
    for sx in (-1, 1):
        x = sx * (IN_L / 2 - 3.5)
        z0 = R_FLOOR + PLATE_POST_UP + POST_GAP + POST_FLANGE_T + 0.05                         # (lid off for this step)
        S[f"svc_plate_screw_{'L' if sx < 0 else 'R'}"] = Cylinder(2.0, R_IN["A"] - 0.3 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, Y_POST, z0)))
    # switch: solder blobs + three wires on its pin tips (the pins point into the bay, just past the Pico's can)
    S["svc_switch_wires"] = on_row(_box(SW_D["l"], 2.5, 2.5, SW_X, SW_U - SW_D["h"] - SW_D["pin_below"] + 0.5, SW_W + SW_D["w"] / 2 - 0.2), "B", x_strip, 0, 0)
    # WS2812 bar leads: three wires off the bar's -X end dropping into the -X rib notch
    y_r, _, z_b = bar_pose()
    S["svc_bar_leads"] = Box(5.0, 5.0, z_b + 2.0 - (R_FLOOR + 5.0 + 0.2), align=(Align.MAX, Align.CENTER, Align.MAX)).moved(
        Location((-N_PIX * WS_D["pitch"] / 2 - 1.0, y_r, z_b + 2.0)))
    # Qi board: coil leads + output wires BESIDE its rib-side edge (no room above it: the lid is 0.3 over the board)
    S["svc_qi_wires"] = on_row(_box(q["board_w"], 4.0, 4.0, 0, 0, 0), "A", xa + 7.4, -1.5 + q["board_l"] / 2 + 2.0, R_FLOOR + c["h"] + 0.2)
    return S


def socket_bank(k, bank):
    """(block, cuts) for a row of wall sockets in row k's +X end wall. Each socket: a block against the wall with an
    open-top pocket (socket drops in from above), two back posts it bears on when the plug is pushed in, a slot
    between them for the pins, and the plug window through the wall."""
    xw = X0 + IN_L                                   # wall inner face
    block, cuts = None, None
    for n, u in bank:
        w_ = JST["sock_w"][n]
        top = SOCK_SHELF + JST["sock_t"] + 0.5
        b = on_row(_box(SOCK_D + SOCK_POST, w_ + 2 * SOCK_POST, top, xw - (SOCK_D + SOCK_POST) / 2, u, 0), k, 0, 0, R_FLOOR)
        c = on_row(_box(SOCK_D + 0.5, w_, 30, xw - SOCK_D / 2 + 0.25, u, SOCK_SHELF), k, 0, 0, R_FLOOR)          # pocket
        c += on_row(_box(SOCK_POST + 0.4, (n - 1) * JST["pitch"] + 2.4, 30, xw - SOCK_D - SOCK_POST / 2, u, SOCK_SHELF), k, 0, 0, R_FLOOR)   # pin slot
        c += on_row(_box(WALL + 4, JST["plug_hole_w"][n], JST["plug_hole_h"], xw + WALL / 2, u,
                         SOCK_SHELF + JST["sock_t"] / 2 - JST["plug_hole_h"] / 2), k, 0, 0, R_FLOOR)              # plug window
        block = b if block is None else block + b
        cuts = c if cuts is None else cuts + c
    if len(bank) == 2 and bank[0][0] == bank[1][0]:   # a same-size pair = one cable: one window, housings glued into one plug
        (n0, u0), (n1, u1) = bank
        w_win = abs(u1 - u0) + (JST["plug_hole_w"][n0] + JST["plug_hole_w"][n1]) / 2
        cuts += on_row(_box(WALL + 4, w_win, JST["plug_hole_h"], xw + WALL / 2, (u0 + u1) / 2,
                            SOCK_SHELF + JST["sock_t"] / 2 - JST["plug_hole_h"] / 2), k, 0, 0, R_FLOOR)
    return block, cuts


# ---------------------------------------------------------------- box
def box():
    body = rounded_outer() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)   # walls stop just under the lid
    body -= skirt_band_cut()                                           # thinned wall top at the ends only
    body -= cavities()
    xa = X0 + CLR
    x_chg = xa + c["w"] / 2 + 2.5          # off the end wall, out of the bay's corner round
    x_batt = xa + c["w"] + CLR + LEAD_GAP + b["l"] / 2 + 2.5
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    # battery bay walls
    wall_h = FOAM_T + 4.0
    # (print 2026-09-24: the ring pressed on the tape lip -> pocket BATT_LIP longer at the lead end, plus a lead notch)
    outer = extrude(RectangleRounded(b["l"] + 2 * BATT_CLR + BATT_LIP + 3.2, b["w"] + 2 * BATT_CLR + 3.2, 3.0), amount=wall_h)
    inner = extrude(RectangleRounded(b["l"] + 2 * BATT_CLR + BATT_LIP, b["w"] + 2 * BATT_CLR, 1.5), amount=wall_h + 1).moved(Location((0, 0, -0.5)))
    ring = (outer - inner).moved(Location((-BATT_LIP / 2, 0, 0)))
    ring -= Box(6.0, 10.0, wall_h + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((-(b["l"] / 2 + BATT_CLR + BATT_LIP + 0.8), 0, -0.5)))                      # lead notch in the -X segment
    body += on_row(ring, "A", x_batt, 0, R_FLOOR) & cavity("A")
    # charger cradle: two corner brackets (pins clipped; wires soldered)
    ck = c["l"] + 2 * CLR
    cr = extrude(RectangleRounded(c["w"] + 2 * CLR + 2.4, ck + 2.4, 1.0), amount=5.0)
    cr -= extrude(Rectangle(c["w"] + 2 * CLR, ck), amount=6).moved(Location((0, 0, -0.5)))
    cr -= Box(c["w"] + 2 * CLR + 6, ck - 8, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -0.5)))
    cr -= Box(c["w"] + 2 * CLR, 6, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, ck / 2 + 1, -0.5)))  # socket end open
    body += on_row(cr, "A", x_chg, CHG_U, R_FLOOR) & cavity("A")
    # strip standoffs with M2 thread-forming holes at the board's drilled holes (rows 2 & 21, columns 1 & 10).
    # Three of them: the -X rib-side corner is where the lid boss stands, so that corner of the strip is snipped
    # and its hole unused.
    for sx in (-1, 1):
        for sy in (-1, 1):
            if sx < 0 and sy < 0:
                continue
            pad = Cylinder(2.1, STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN))
            if sx < 0:   # row 2 sits beside the Pico's row-2 pins: flatten the pad's inboard side clear of their solder
                pad -= Box(6, 6, 10, align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Location((0, -sy * (s["standoff_u"] - 9.95) * sy * sy - (s["standoff_u"] - 9.95) * 0 - (s["standoff_u"] - 9.95), 0, -1))) if False else Box(6, 6, 10, align=(Align.CENTER, Align.MAX if sy > 0 else Align.MIN, Align.MIN)).moved(Location((0, (9.95 - s["standoff_u"]) * sy, -1)))
            body += on_row(pad, "B", x_strip + sx * s["standoff_x"], sy * s["standoff_u"], R_FLOOR)
            body -= on_row(Cylinder(M2_FORM_D / 2, STANDOFF + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), "B",
                           x_strip + sx * s["standoff_x"], sy * s["standoff_u"], R_FLOOR - 1.0)   # blind: 1 mm into the floor
    # lid bosses with M2 heat-set inserts: -X on the ridge line (strip side), +X in row B's chest corner (the rib
    # corner there holds the cord socket). The +X boss is built in the row frame, so its screw is normal to that facet.
    x = -(IN_L / 2 - 3.5)
    body += Cylinder(LID_BOSS_D / 2, 200).moved(Location((x, Y_BOSS, 0))) & outer_form() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)
    body -= Cylinder(LID_BOSS_HOLE / 2, 4.6, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
        Location((x, Y_BOSS, tent_z(Y_BOSS, R_IN["A"] - 0.2, R_IN["B"] - 0.2) + 0.01)))
    x = IN_L / 2 - 3.5
    boss_h = R_IN["B"] - 0.2 - R_FLOOR
    body += on_row(Cylinder(LID_BOSS_D / 2, boss_h, align=(Align.CENTER, Align.CENTER, Align.MIN)), "B",
                   x, CHEST_BOSS_U, R_FLOOR) & outer_form()
    body -= on_row(Cylinder(LID_BOSS_HOLE / 2, 4.6 + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)), "B",
                   x, CHEST_BOSS_U, R_IN["B"] - 0.2 - 4.6)
    body -= skirt_band_cut()                                           # bosses must not fill the skirt lap
    # plate posts (battery side): each comes up through the floor into a boss whose 1.5 mm top web the M2x6
    # clamps onto the post's heat-set insert (print 2026-09-24: the old post stood proud of the floor, so the
    # head landed on the brass and nothing clamped the box). Above the web a 4.5 bore takes the head + driver.
    for sx in (-1, 1):
        x = sx * (IN_L / 2 - 3.5)
        top = R_FLOOR + PLATE_POST_UP + POST_GAP + POST_FLANGE_T
        body += Cylinder(POST_BOSS_D / 2, top - R_FLOOR + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, Y_POST, R_FLOOR - 1.0))) & outer_form() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)
        body -= Cylinder(PLATE_POST_D / 2 + 0.3, 200, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
            Location((x, Y_POST, R_FLOOR + PLATE_POST_UP + POST_GAP)))                      # post pocket, from below
        body -= Cylinder(POST_BORE_D / 2, 200, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, Y_POST, top - 0.01)))                                                # head + driver bore
        body -= Cylinder(M2["clear_d"] / 2, 200).moved(Location((x, Y_POST, 0)))               # screw through the web
    # coil pocket: the coil is wider than the battery bay, so notch the rib top where it overhangs
    body -= on_row(qi_coil_pocket(), "A", x_batt, COIL_U, R_IN["A"] - q["coil_t"] - q["ferrite_t"] - 0.4)
    # light-line channel: the bar hangs from the lid into the rib between the bays; pocket the rib for it
    y_r, z_in, z_b = bar_pose()
    body -= Box(N_PIX * WS_D["pitch"] + 2.0, WS_D["w"] + 1.2, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, y_r, z_b - 0.6)))
    # wire notch through the middle wall at the USB end: VBUS->VI, VO->switch, JST+ ->divider, GND cross here
    # it starts right at the lid boss (no thin fin between them) and runs 9 mm along the wall
    nx0 = -(IN_L / 2 - 3.5) + LID_BOSS_D / 2 - 0.2
    body -= Box(9.0, NOTCH_W, 30, align=(Align.MIN, Align.CENTER, Align.MIN)).moved(Location((nx0, Y_RIB, R_FLOOR + 5.0)))
    body += Cylinder(LID_BOSS_D / 2, 200).moved(Location((-(IN_L / 2 - 3.5), Y_BOSS, 0))) & outer_form() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)             - Cylinder(LID_BOSS_HOLE / 2, 4.6, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
                Location((-(IN_L / 2 - 3.5), Y_BOSS, tent_z(Y_BOSS, R_IN["A"] - 0.2, R_IN["B"] - 0.2) + 0.01)))             - skirt_band_cut()
    # openings
    P = placements()
    body -= usb_cuts()
    body -= nub_slot()
    # switch mount (print 2026-09-24: the 3 mm ledge drooped and hung over the perf's outer hole column). Now two
    # fins on the chest wall, 1 mm into the bay - clear of every perf hole - each with a 1 mm foot the switch's ends
    # rest on. Body glued between the fins, nub through the slot.
    u_fin = ROW_W["B"] / 2 - 0.7 + 0.8                          # fins stand 0.7 into the bay (the strip still drops past them), 0.9 into the wall
    for sx in (-1, 1):
        xf = x_strip + SW_X + sx * (SW_D["l"] / 2 + 0.5 + 0.6)
        body += on_row(Box(1.2, 1.6, R_IN["B"] - 0.2 - (W_STRIP + s["t"] + 0.5), align=(Align.CENTER, Align.CENTER, Align.MIN)),
                       "B", xf, u_fin, W_STRIP + s["t"] + 0.5) & cavity("B")
        body += on_row(Box(1.5, 1.6, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)),
                       "B", xf - sx * 1.35, u_fin, SW_W - 1.0) & cavity("B")                   # foot under the switch end
    body -= nub_notch()
    # +X notch through the middle wall: the trunk wires cross from the row A sockets to the strip; also the
    # screwdriver path to the +X plate post
    body -= Box(9.0, NOTCH_W, 30, align=(Align.MAX, Align.CENTER, Align.MIN)).moved(Location((IN_L / 2 - 2.0, Y_RIB, R_FLOOR + 5.0)))
    # wall sockets
    for k, bank in (("A", TRUNK_A), ("B", ROW_B_SOCKETS)):
        blk, cut = socket_bank(k, bank)
        body += blk & cavity(k)
        body -= cut
    return body


def usb_cuts():
    """Shell-sized hole through the -X wall plus the overmold recess limited to the outer recess_d of the wall."""
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    x_pico = x_strip + s["pico_row_offset"]
    w_usb = W_STRIP + s["t"] + DIM["pico"]["hdr_base"]
    return on_row(usb_wall_cut(), "B", x_pico, 0, w_usb)


def qi_coil_pocket():
    from rk_parts import DIM as _D
    d = _D["qi"]
    sk = RectangleRounded(d["coil_l"] + 1.2, d["coil_w"] + 1.2, d["coil_w"] / 2 + 0.59)
    return extrude(sk, amount=10)


def nub_slot():
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    return on_row(Box(SW_D["slot_l"], 2 * WALL + 4, SW_D["slot_w"]), "B",
                  x_strip + SW_X, ROW_W["B"] / 2 + WALL / 2, SW_W + SW_D["w"] / 2)      # Box is centre-aligned


def nub_notch():
    """Finger recess in the outer chest wall so the nub sits below the surface (nothing protrudes)."""
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    depth = max(NOTCH_D, 0.4)
    return on_row(Box(SW_D["slot_l"] + 8, depth, 7.0), "B",
                  x_strip + SW_X, ROW_W["B"] / 2 + WALL - depth / 2, SW_W + SW_D["w"] / 2)


def lid():
    cap = rounded_outer() - tent(R_IN["A"], R_IN["B"])                                   # the cap itself
    skirt = ((rounded_outer() - parting_solid()) & tent(R_IN["A"], R_IN["B"]) & end_zone()) - outer_form(inset=SKIRT_T)
    cap += skirt                                                                          # skirt at the ends only
    P = placements()
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    cap -= usb_cuts()
    cap -= nub_slot()
    cap -= nub_notch()
    # LED window: the LED stands on the strip; its dome shows through a plain hole (tip ~0.9 below the surface)
    cap -= on_row(Cylinder(LED_D["dome_d"] / 2 + 0.3, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), "B",
                  x_strip + LED_X, LED_Y, R_IN["B"] - 1.0)
    # light line: one slit-window per pixel, thinned from the outside down to SLIT_T above the inner ridge apex
    y_r, z_in, _ = bar_pose()
    for i in range(N_PIX):
        px = (i - (N_PIX - 1) / 2) * WS_D["pitch"]
        cap -= Box(SLIT_L, SLIT_W, 20, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((px, y_r, z_in + SLIT_T)))
    cap -= Cylinder(SCREW_D / 2, 200).moved(Location((-(IN_L / 2 - 3.5), Y_BOSS, 0)))
    cap -= on_row(Cylinder(SCREW_D / 2, 40), "B", IN_L / 2 - 3.5, CHEST_BOSS_U, R_IN["B"])
    return cap


def shell_outer():
    """Closed outer envelope (for the containment check)."""
    return rounded_outer() - nub_notch()


def summary():
    return dict(outer=(round(OUT_L, 1), round(OUT_W, 1)), r_out=dict((k, round(v, 1)) for k, v in R_OUT.items()),
                r_in=dict((k, round(v, 1)) for k, v in R_IN.items()), y_rows=dict((k, round(v, 1)) for k, v in Y_ROW.items()))
