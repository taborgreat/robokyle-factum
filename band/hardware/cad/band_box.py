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
LID_BOSS_D, LID_BOSS_HOLE = 6.4, 3.2          # full-round bosses with M2 heat-set inserts; M2x6 from the lid
M2_FORM_D = DIM["m2"]["thread_form_d"]
PLATE_POST_D, PLATE_POST_UP = 6.2, 0.7        # the plate's posts poke this far above the floor; M2x6 from inside
SERVICE_A = 0.4     # air above the coil
LED_PROUD = 1.2     # LED dome tip above the lid (Tabor: ~1 mm is fine); keeps the lid boss above the Pico edge

b, s, c, q = DIM["batt"], DIM["strip"], DIM["charger"], DIM["qi"]
SW_D, LED_D, WS_D = DIM["switch"], DIM["led"], DIM["ws2812"]
LED_X, LED_Y = 18.0, 11.6      # LED on the strip's chest margin row (strip coords)
N_PIX = 3                      # WS2812 pixels on the crest (4 would run into the ridge screws)
BAR_GAP = 2.2                  # air between the bar's top (the LEDs) and the lid's inner ridge apex
SLIT_L, SLIT_W, SLIT_T = 8.0, 3.0, 0.8   # one thinned slit-window per pixel; SLIT_T = plastic left over the LED
SW_X, SW_W = 8.0, 11.0         # switch along the chest wall; body bottom height above the arm
SW_INSET = 1.0                 # nub base this far inside the wall's inner face
CHG_U = -4.0                   # charger shifted toward the triceps wall: battery plug clears the rib and the -X plate post
MOTOR_U = -7.5
COIL_U = 2.0                   # coil shifted toward the rib (it is wider than the battery bay)
CUP_WALL = 1.2                 # button cup wall (was 1.5; the cup now shares the end wall with the cord socket)
CUP_LEG_CLR = 0.8              # the button's legs stand ~0.3 proud of its +-X faces
BTN_LEG = 1.5                  # clip the button's legs to this (stock 3.5 would hit the floor); wires soldered sideways
BTN_RECESS_D, BTN_RECESS = 18.0, 0.8   # shallow round pocket in the floor under the button: leg + blob room
# wall sockets (straight JST-PH headers lying on their backs in pockets behind the +X end wall; plug window = the
# gauge's plug slot, so the wall is the flange; a dab of hot glue keeps them from lifting)
JST = DIM["jst_ph"]
SOCK_D, SOCK_POST, SOCK_SHELF = JST["sock_d"] + 0.2, 1.2, 1.0    # pocket depth, back-post thickness, shelf above the floor
SOCK_PIN = 2.0                 # socket pins clipped to 2 mm (the trunk pins would otherwise reach the battery ring)
SOCK_ZONE = 3.0                # extra bay length at the +X end so the socket pins clear the battery ring
TRUNK = [(4, -6.875), (4, 4.575)]        # row A end wall: trunk plug A (3V3 GND EMG1 EMG2), trunk plug B (SDA SCL INT RST)
CORD = [(3, -11.125)]                    # row B end wall, rib side: hand cord (TX RX GND)
NOTCH_W = 17.0                 # middle-wall notches: wider than the wall's leaning faces at the top (13.3), no fins left
LID_SOCK_X, LID_SOCK_U = 25.6, (-6.5, 3.0)   # two upright PH3 sockets on the strip, pins in row 21 bent 1.2 toward +X
                                              # (body clear of the Pico's end and of the button cup), strip coords

# ---------------------------------------------------------------- row geometry
ROW_W = {"A": b["w"] + 2 * BATT_CLR, "B": s["w"] + 2 * CLR}
IN_W = ROW_W["A"] + RIB + ROW_W["B"]
Y_ROW = {"A": -IN_W / 2 + ROW_W["A"] / 2, "B": IN_W / 2 - ROW_W["B"] / 2}
LEAD_GAP = 4.0
BATT_LIP = 2.0                 # the cell's tape lip (3.7, soft) at the lead end: the ring pocket is this much longer there (2.0 = all the room before the charger)
BTN_ZONE = DIM["button"]["l"] + 2 * CLR + 2 * CUP_WALL + 1.0 + SOCK_ZONE   # button cup + socket room beyond the strip's +X end
USB_NOSE = DIM["usb_plug"]["nose_in"]                        # the Pico's USB socket pokes this far into the wall hole
USB_FACE_REL = (s["pico_row_offset"] - DIM["pico"]["l"] / 2 - DIM["pico"]["usb_overhang"]) + s["l"] / 2   # USB face vs strip end (- = past it)
STRIP_X0 = -USB_NOSE - USB_FACE_REL                            # strip's -X end relative to the wall's inner face
ROW_L = {"A": CLR + c["w"] + CLR + LEAD_GAP + b["l"] + CLR, "B": STRIP_X0 + s["l"] + CLR + BTN_ZONE}
IN_L = max(ROW_L.values())
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
X0 = -IN_L / 2

# radial stack (heights above the arm surface)
W_BATT = R_FLOOR + FOAM_T
W_STRIP = R_FLOOR + STANDOFF
TOP_A = W_BATT + b["h"] + q["ferrite_t"] + q["coil_t"]
USB_TOP = W_STRIP + s["t"] + DIM["pico"]["hdr_base"] + DIM["pico"]["t"] + DIM["pico"]["usb_h"] / 2 + DIM["usb_plug"]["h"] / 2
R_IN = {"A": TOP_A + SERVICE_A, "B": USB_TOP + 0.3}         # lid underside per row: the USB plug sets row B
BTN_D = DIM["button"]
BTN_X = s["l"] / 2 + CLR + (BTN_ZONE - SOCK_ZONE) / 2 - 0.5  # button (in the lid) beyond the strip's +X end, strip coords
BTN_U = 2.35                                                   # shifted to the chest side: the cord socket sits on the rib side
BTN_W = R_IN["B"] + LID_T - BTN_D["cap_h"] - BTN_D["h"]      # body bottom height: cap flush with the lid surface
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
    P["strip"] = on_row(pico_on_strip(), "B", x_strip, 0, W_STRIP)
    x_pico = x_strip + s["pico_row_offset"]
    P["usb_plug"] = on_row(pico_usb_plug(), "B", x_pico, 0, W_STRIP + s["t"] + DIM["pico"]["hdr_base"])
    P["button"] = on_row(tactile_button(leg_below=BTN_LEG), "B", x_strip + BTN_X, BTN_U, BTN_W)   # legs clipped
    P["button_keepout"] = on_row(tactile_button_keepout(), "B", x_strip + BTN_X, BTN_U, BTN_W)
    P["led"] = on_row(led_5mm(), "B", x_strip + LED_X, LED_Y, R_OUT["B"] + LED_PROUD - LED_D["body_h"])
    y_r, _, z_b = bar_pose()
    P["ws2812"] = ws2812_segment(N_PIX).moved(Location((0, y_r, z_b)))          # along the crest, global frame
    P["motor"] = on_row(coin_motor(), "B", x_strip + 2, MOTOR_U, R_IN["B"] - DIM["motor"]["h"], rz=180)   # tab + leads toward the USB end
    # switch: nub toward +u through the chest wall; origin at the nub base; body 1 mm inside the wall so the
    # nub tip is flush with the outer surface (and 0.6 recessed inside the finger notch)
    sw = slide_switch().rotate(Axis.X, -90).moved(Location((0, -SW_D["h"], 0)))
    P["switch"] = on_row(sw, "B", x_strip + SW_X, SW_U, SW_W + SW_D["w"] / 2)
    for k, bank in (("A", TRUNK), ("B", CORD)):
        for i, (n, u) in enumerate(bank):
            sk = jst_socket(n) - _box(10, 20, 10, -JST["sock_d"] - SOCK_PIN - 5, 0, -1)       # pins clipped
            P[f"sock_{k}{i}"] = on_row(sk, k, X0 + IN_L, u, R_FLOOR + SOCK_SHELF)
    # lid pigtail: two PH3 sockets soldered upright on the strip's free row 21 (pins bent to the 2.54 grid);
    # the lid's six wires (GND, 3V3, LED+, BTN, MOTOR, DIN) end in two PH3 housings so the lid comes right off
    up = (jst_socket(3) - _box(10, 20, 10, -JST["sock_d"] - SOCK_PIN - 5, 0, -1)).rotate(Axis.Y, -90).moved(Location((0, 0, JST["sock_d"])))   # opening up
    for i, u in enumerate(LID_SOCK_U):
        P[f"sock_L{i}"] = on_row(up, "B", x_strip + LID_SOCK_X, u, W_STRIP + s["t"])
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
    for k, bank in (("A", TRUNK), ("B", CORD)):
        for i, (n, u) in enumerate(bank):
            z = _box(2.2, (n - 1) * JST["pitch"] + 2.6, 4.0, -(JST["sock_d"] + SOCK_PIN) - 1.1, 0, SOCK_SHELF + JST["sock_t"] / 2 - 2.0)
            S[f"svc_sock_{k}{i}"] = on_row(z, k, X0 + IN_L, u, R_FLOOR)
    # strip: tall parts (transistor, diodes, resistors on end) up to 4.5 mm on the two outer rows beside the Pico.
    # Rib side: from 20 mm before the strip centre (the -X corner is snipped for the lid boss) to the free rows.
    # Chest side: same, minus the switch's and the LED's shadows - keep those spots for low parts.
    S["svc_strip_margin_rib"] = on_row(_box(43.0, 4.0, 4.5, 1.5, -12.7, s["t"]), "B", x_strip, 0, W_STRIP)
    chest = _box(43.0, 4.0, 4.5, 1.5, 12.7, s["t"])
    chest -= _box(SW_D["l"] + 3.0, 6.0, 6.0, SW_X, 12.7, s["t"] - 0.5)
    chest -= _box(LED_D["flange_d"] + 3.2 + 1.0, 6.0, 6.0, LED_X, 12.7, s["t"] - 0.5)
    S["svc_strip_margin_chest"] = on_row(chest, "B", x_strip, 0, W_STRIP)
    # lid pigtail: the two PH3 housings' wires bending over right above each socket (2 mm)
    for i, u in enumerate(LID_SOCK_U):
        S[f"svc_lid_plug_{i}"] = on_row(_box(5.0, 8.5, 2.0, LID_SOCK_X, u, s["t"] + JST["sock_d"]), "B", x_strip, 0, W_STRIP)
    # lid wires: a flat ribbon under the lid down the Pico's centre line (the only lane past the motor ring), from
    # the plugs to the motor; plus a short chest-side run to the LED boss
    S["svc_lid_wires_mid"] = on_row(_box(LID_SOCK_X - 2.0 + 6.0, 4.0, 1.5, (LID_SOCK_X - 2.0 - 6.0) / 2, 1.5, 0), "B", x_strip, 0, R_IN["B"] - 1.6)   # u +1.5: just clear of the motor ring
    S["svc_lid_wires_chest"] = on_row(_box(LID_SOCK_X - 2.0 - (LED_X + 4.5), 3.0, 1.5, (LID_SOCK_X - 2.0 + LED_X + 4.5) / 2, LED_Y, 0), "B", x_strip, 0, R_IN["B"] - 1.6)
    # button: clipped legs + solder blobs under the body, two wires leaving sideways (-X, toward the lid sockets)
    S["svc_button_solder"] = on_row(_box(BTN_D["leg_dx"] + 2.0, BTN_D["leg_dy"] + 2.0, BTN_LEG + 0.5, BTN_X, BTN_U, BTN_W - BTN_LEG - 1.0), "B", x_strip, 0, 0)   # blobs at the leg tips, below the cup
    S["svc_button_wires"] = on_row(_box(10.0, 4.0, 1.4, BTN_X - BTN_D["leg_dx"] / 2 - 5.0, BTN_U, BTN_W - BTN_LEG - 1.2), "B", x_strip, 0, 0)
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
    if len(bank) == 2:   # two sockets side by side: one window, so the two housings can be glued into one plug
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
    # strip standoffs with M2 thread-forming holes (drill the perf 2.2 mm at these spots)
    for sx in (-1, 1):
        for sy in (-1, 1):
            body += on_row(Cylinder(2.25, STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN)), "B",
                           x_strip + sx * s["standoff_x"], sy * s["standoff_u"], R_FLOOR)
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
    # holes in the floor for the plate's posts (battery side): M2x6 from inside into the insert on each post
    for sx in (-1, 1):
        x = sx * (IN_L / 2 - 3.5)
        body -= Cylinder(PLATE_POST_D / 2 + 0.3, 200).moved(Location((x, Y_POST, 0)))
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
    # floor recess under the button's clipped legs + solder (the plate is right below: 0.8 mm of floor left there)
    body -= on_row(Cylinder(BTN_RECESS_D / 2, BTN_RECESS + 10, align=(Align.CENTER, Align.CENTER, Align.MAX)), "B",
                   x_strip + BTN_X, BTN_U, R_FLOOR + 10.0) & cavity("B")
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
    for k, bank in (("A", TRUNK), ("B", CORD)):
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
    # button pocket: a square cup on the underside holds the body (press fit), the cap passes the lid hole
    cup_h = R_IN["B"] - (BTN_W - 0.5) + 0.05                    # from 0.5 below the button body up to the lid underside
    # (print 2026-09-24: the four solder legs sit on the body's +-X faces and hang out of the cup's open bottom,
    #  so the cup is CUP_LEG_CLR wider along X and the old wire slots are gone)
    cup = Box(BTN_D["l"] + 2 * CUP_LEG_CLR + 2 * CUP_WALL, BTN_D["w"] + 2 * CLR + 2 * CUP_WALL, cup_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cup -= Box(BTN_D["l"] + 2 * CUP_LEG_CLR, BTN_D["w"] + 2 * CLR, cup_h + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -1)))
    cap = Compound([cap]) + (on_row(cup, "B", x_strip + BTN_X, BTN_U, BTN_W - 0.5) & cavity_inset("B", 0.3))
    cap -= P["button_keepout"]
    cap -= usb_cuts()
    cap -= nub_slot()
    cap -= nub_notch()
    # coin motor: a locating ring on the underside (the motor's own adhesive pad holds it); gap for the tab + leads (-X)
    mr = Cylinder(DIM["motor"]["cradle_id"] / 2 + 1.2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
    mr -= Cylinder(DIM["motor"]["cradle_id"] / 2, 3.0, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(Location((0, 0, 1)))
    mr -= Box(6.0, DIM["motor"]["tab_w"] + 1.0, 3.0, align=(Align.MAX, Align.CENTER, Align.MAX)).moved(Location((-DIM["motor"]["d"] / 2 + 1.0, 0, 1)))
    cap = Compound([cap]) + (on_row(mr, "B", x_strip + 2, MOTOR_U, R_IN["B"] + 0.01) & cavity_inset("B", 0.3))
    # LED boss on the underside: flange seats on its bottom, dome passes a dome-sized hole, tip LED_PROUD outside
    boss_h = LED_D["body_h"] - LED_PROUD - LED_D["flange_t"]
    cap = Compound([cap]) + (on_row(Cylinder(LED_D["dome_d"] / 2 + 1.6, boss_h, align=(Align.CENTER, Align.CENTER, Align.MAX)), "B",
                  x_strip + LED_X, LED_Y, R_OUT["B"]) & cavity_inset("B", 0.3))
    cap -= on_row(Cylinder(LED_D["hole"] / 2, boss_h + 2, align=(Align.CENTER, Align.CENTER, Align.MAX)), "B",
                  x_strip + LED_X, LED_Y, R_OUT["B"] + 1)
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
