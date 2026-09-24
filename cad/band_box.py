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
from build123d import (Box, Cylinder, Location, Align, Axis, Rectangle, RectangleRounded, extrude, fillet)
from rk_parts import (DIM, pico_on_strip, pico_usb_plug, usb_wall_cut, battery, charger, charger_keepout, slide_switch,
                      tactile_button, tactile_button_keepout, led_5mm, ws2812_segment, coin_motor, qi_coil, qi_board)

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
SKIRT, SKIRT_T, SKIRT_CLR = 4.0, 1.0, 0.15    # lid skirt height / thickness / clearance over the thinned wall
SCREW_D, BOSS_D = 2.3, 5.0
M2_FORM_D = DIM["m2"]["thread_form_d"]
PLATE_BOSS_D, PLATE_BOSS_H = 6.2, 4.5         # the plate's heat-set bosses (band_plate.py) poke through the floor
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
CHG_U = -3.0                   # charger shifted toward the triceps wall so the battery plug clears the rib side
MOTOR_U = -7.5
COIL_U = 2.0                   # coil shifted toward the rib (it is wider than the battery bay)

# ---------------------------------------------------------------- row geometry
ROW_W = {"A": b["w"] + 2 * BATT_CLR, "B": s["w"] + 2 * CLR}
IN_W = ROW_W["A"] + RIB + ROW_W["B"]
Y_ROW = {"A": -IN_W / 2 + ROW_W["A"] / 2, "B": IN_W / 2 - ROW_W["B"] / 2}
LEAD_GAP = 4.0
BTN_ZONE = DIM["button"]["l"] + 2 * CLR + 3.0 + 1.0          # button cup beyond the strip's +X end
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
BTN_X, BTN_U = s["l"] / 2 + CLR + BTN_ZONE / 2 - 0.5, 0.0    # button (in the lid) beyond the strip's +X end, strip coords
BTN_W = R_IN["B"] + LID_T - BTN_D["cap_h"] - BTN_D["h"]      # body bottom height: cap flush with the lid surface
R_OUT = {k: v + LID_T for k, v in R_IN.items()}
PARTING = {k: v - SKIRT for k, v in R_IN.items()}
SW_U = ROW_W["B"] / 2 - SW_INSET
NOTCH_D = SW_D["nub_h"] - SW_INSET - WALL + 0.6      # finger recess depth (nub tip 0.6 below the surface)
Y_RIB = (Y_ROW["A"] + ROW_W["A"] / 2 + Y_ROW["B"] - ROW_W["B"] / 2) / 2      # global y of the rib centre at floor
Y_BOSS = Y_RIB + 4.5      # ridge screws sit toward the strip side: snip the strip's two rib-side corners ~4 mm


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


def cavities():
    return cavity("A") + cavity("B")


def parting_solid():
    return tent(PARTING["A"], PARTING["B"])


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


def bar_pose():
    """Global position of the WS2812 bar: centred on the crest, top BAR_GAP below the inner ridge apex."""
    y_r, z_in = ridge(R_IN["A"], R_IN["B"])
    z_bottom = z_in - BAR_GAP - WS_D["t"] - WS_D["led_h"]
    return y_r, z_in, z_bottom


# ---------------------------------------------------------------- part placement
def placements():
    P = {}
    xa = X0 + CLR
    x_chg = xa + c["w"] / 2
    x_batt = xa + c["w"] + CLR + LEAD_GAP + b["l"] / 2
    P["charger"] = on_row(charger(), "A", x_chg, CHG_U, R_FLOOR, rz=-90)          # crosswise; socket toward the rib (+u)
    P["charger_keepout"] = on_row(charger_keepout(), "A", x_chg, CHG_U, R_FLOOR, rz=-90)
    P["battery"] = on_row(battery(), "A", x_batt, 0, W_BATT)
    P["qi_board"] = on_row(qi_board(), "A", xa + q["board_w"] / 2, 2.0, R_IN["A"] - q["board_t"], rz=90)
    P["qi_coil"] = on_row(qi_coil(), "A", x_batt, COIL_U, R_IN["A"] - q["coil_t"] - q["ferrite_t"])
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    P["strip"] = on_row(pico_on_strip(), "B", x_strip, 0, W_STRIP)
    x_pico = x_strip + s["pico_row_offset"]
    P["usb_plug"] = on_row(pico_usb_plug(), "B", x_pico, 0, W_STRIP + s["t"] + DIM["pico"]["hdr_base"])
    P["button"] = on_row(tactile_button(), "B", x_strip + BTN_X, BTN_U, BTN_W)
    P["button_keepout"] = on_row(tactile_button_keepout(), "B", x_strip + BTN_X, BTN_U, BTN_W)
    P["led"] = on_row(led_5mm(), "B", x_strip + LED_X, LED_Y, R_OUT["B"] + LED_PROUD - LED_D["body_h"])
    y_r, _, z_b = bar_pose()
    P["ws2812"] = ws2812_segment(N_PIX).moved(Location((0, y_r, z_b)))          # along the crest, global frame
    P["motor"] = on_row(coin_motor(), "B", x_strip + 2, MOTOR_U, R_IN["B"] - DIM["motor"]["h"], rz=180)   # tab + leads toward the USB end
    # switch: nub toward +u through the chest wall; origin at the nub base; body 1 mm inside the wall so the
    # nub tip is flush with the outer surface (and 0.6 recessed inside the finger notch)
    sw = slide_switch().rotate(Axis.X, -90).moved(Location((0, -SW_D["h"], 0)))
    P["switch"] = on_row(sw, "B", x_strip + SW_X, SW_U, SW_W + SW_D["w"] / 2)
    return P


# ---------------------------------------------------------------- box
def box():
    body = rounded_outer() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)   # walls stop just under the lid
    body -= (outer_form() - outer_form(inset=SKIRT_T + SKIRT_CLR)) - parting_solid()   # thinned wall top
    body -= cavities()
    xa = X0 + CLR
    x_chg = xa + c["w"] / 2
    x_batt = xa + c["w"] + CLR + LEAD_GAP + b["l"] / 2
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    # battery bay walls
    wall_h = FOAM_T + 4.0
    outer = extrude(RectangleRounded(b["l"] + 2 * BATT_CLR + 3.2, b["w"] + 2 * BATT_CLR + 3.2, 3.0), amount=wall_h)
    inner = extrude(RectangleRounded(b["l"] + 2 * BATT_CLR, b["w"] + 2 * BATT_CLR, 1.5), amount=wall_h + 1).moved(Location((0, 0, -0.5)))
    body += on_row(outer - inner, "A", x_batt, 0, R_FLOOR) & cavity("A")
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
    # ridge screw bosses in the end walls; the plate's insert bosses come up through the floor into them
    for sx in (-1, 1):
        x = sx * (IN_L / 2 - 1.0)
        body += Cylinder(BOSS_D / 2, 200).moved(Location((x, Y_BOSS, 0))) & cavities() & tent(R_IN["A"] - 0.2, R_IN["B"] - 0.2)
        body -= Cylinder(SCREW_D / 2, 200).moved(Location((x, Y_BOSS, 0)))
        body -= Cylinder(PLATE_BOSS_D / 2 + 0.3, PLATE_BOSS_H + 0.2 + 5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, Y_RIB, -5))) & arm_cyl(PLATE_BOSS_H + 0.2)
    # coil pocket: the coil is wider than the battery bay, so notch the rib top where it overhangs
    body -= on_row(qi_coil_pocket(), "A", x_batt, COIL_U, R_IN["A"] - q["coil_t"] - q["ferrite_t"] - 0.4)
    # light-line channel: the bar hangs from the lid into the rib between the bays; pocket the rib for it
    y_r, z_in, z_b = bar_pose()
    body -= Box(N_PIX * WS_D["pitch"] + 2.0, WS_D["w"] + 1.2, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, y_r, z_b - 0.6)))
    # wire notch through the middle wall at the USB end: VBUS->VI, VO->switch, JST+ ->divider, GND cross here
    body -= Box(9.0, 14.0, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((X0 + 12.0, Y_RIB, R_FLOOR + 5.0)))
    # openings
    P = placements()
    body -= usb_cuts()
    body -= nub_slot()
    body += on_row(Box(SW_D["l"] + 2, 3.0, 1.5), "B", x_strip + SW_X, ROW_W["B"] / 2 - 1.5, SW_W - 0.75)  # switch ledge (pocket 9.2 x 4.3 per gauge)
    body -= nub_notch()
    body -= on_row(Cylinder(3.0, 10).rotate(Axis.Y, 90), "B", IN_L / 2, -4.0, R_FLOOR + 6.0)   # trunk exit, +X wall
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
    cap = rounded_outer() - parting_solid()
    cap -= outer_form(inset=SKIRT_T) & tent(R_IN["A"], R_IN["B"]) - parting_solid()   # hollow skirt
    cap -= cavities() & tent(R_IN["A"], R_IN["B"])
    P = placements()
    x_strip = X0 + STRIP_X0 + s["l"] / 2
    # button pocket: a square cup on the underside holds the body (press fit), the cap passes the lid hole
    cup = Box(BTN_D["l"] + 2 * CLR + 3.0, BTN_D["w"] + 2 * CLR + 3.0, BTN_D["h"] + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cup -= Box(BTN_D["l"] + 2 * CLR, BTN_D["w"] + 2 * CLR, BTN_D["h"] + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -1)))
    cup -= Box(BTN_D["l"] + 2 * CLR + 4, 4.0, BTN_D["h"] + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -1)))  # wire exits
    cap += on_row(cup, "B", x_strip + BTN_X, BTN_U, BTN_W - 0.5) & cavity("B")
    cap -= P["button_keepout"]
    cap -= usb_cuts()
    cap -= nub_slot()
    cap -= nub_notch()
    # LED boss on the underside: flange seats on its bottom, dome passes a dome-sized hole, tip LED_PROUD outside
    boss_h = LED_D["body_h"] - LED_PROUD - LED_D["flange_t"]
    cap += on_row(Cylinder(LED_D["dome_d"] / 2 + 1.6, boss_h, align=(Align.CENTER, Align.CENTER, Align.MAX)), "B",
                  x_strip + LED_X, LED_Y, R_OUT["B"]) & cavity("B")
    cap -= on_row(Cylinder(LED_D["hole"] / 2, boss_h + 2, align=(Align.CENTER, Align.CENTER, Align.MAX)), "B",
                  x_strip + LED_X, LED_Y, R_OUT["B"] + 1)
    # light line: one slit-window per pixel, thinned from the outside down to SLIT_T above the inner ridge apex
    y_r, z_in, _ = bar_pose()
    for i in range(N_PIX):
        px = (i - (N_PIX - 1) / 2) * WS_D["pitch"]
        cap -= Box(SLIT_L, SLIT_W, 20, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((px, y_r, z_in + SLIT_T)))
    for sx in (-1, 1):
        cap -= Cylinder(SCREW_D / 2, 200).moved(Location((sx * (IN_L / 2 - 1.0), Y_BOSS, 0)))
    return cap


def shell_outer():
    """Closed outer envelope (for the containment check)."""
    return rounded_outer() - nub_notch()


def summary():
    return dict(outer=(round(OUT_L, 1), round(OUT_W, 1)), r_out=dict((k, round(v, 1)) for k, v in R_OUT.items()),
                r_in=dict((k, round(v, 1)) for k, v in R_IN.items()), y_rows=dict((k, round(v, 1)) for k, v in Y_ROW.items()))
