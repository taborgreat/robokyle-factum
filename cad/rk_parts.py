"""Robo Kyle parts library: every real part as a named build123d solid at the origin.

Conventions
- Units mm. Each part is built with its mounting face on Z=0 and grows +Z (board bottom on Z=0, components up).
- X is the part's long axis. Connectors/cables exit where noted in the docstring.
- `SRC` records where each number came from: "datasheet", "measured" (Tabor), "guess" (must be verified
  with the fit gauge or a ruler before the box is printed). Do not silently promote a guess.
- `keepout()` returns the part solid plus the volume a plug/cable/finger needs; pockets are cut from
  keepouts, never from bare parts.

Confidence key: D = datasheet, M = measured by Tabor, G = guess.
"""
from build123d import (Box, Cylinder, Compound, Location, Align, Plane, Axis, Part, Solid,
                       fillet, Rectangle, extrude, Sketch)

A0 = (Align.CENTER, Align.CENTER, Align.MIN)   # centered in XY, base on Z=0


def _box(l, w, h, x=0, y=0, z=0):
    return Box(l, w, h, align=A0).moved(Location((x, y, z)))


def _cyl(d, h, x=0, y=0, z=0):
    return Cylinder(d / 2, h, align=A0).moved(Location((x, y, z)))


# --------------------------------------------------------------------------------------------
# Dimensions. Keep every number here so the box script never carries magic numbers.
# --------------------------------------------------------------------------------------------
DIM = {
    # Raspberry Pi Pico W (datasheet mechanical drawing)
    "pico": dict(l=51.0, w=21.0, t=1.0, hole_d=2.1, hole_dx=47.0, hole_dy=11.4,
                 usb_w=8.0, usb_d=5.6, usb_h=2.8, usb_overhang=1.3,      # micro-USB receptacle, -X end
                 shield_l=12.0, shield_w=12.0, shield_h=2.0,               # CYW43439 can, +X end (antenna beyond it)
                 comp_h=1.6,                                               # tallest passives elsewhere
                 hdr_pitch=2.54, hdr_base=2.5, hdr_pin_below=3.0, SRC="D"),
    # micro-USB plug, overmold envelope (typical cable)
    "usb_plug": dict(w=10.8, h=7.2, l=22.0, insert=6.0, SRC="G"),
    # Perfboard strip the Pico is soldered onto (Tabor: 25x60 snapped from ELEGOO 4x6 cm board)
    # 64 = Pico 51 + 13 mm zone at the +X end for the 12 mm button; small parts go on the outer rows beside the Pico.
    # 10 x 25 holes of 2.54 mm perf, snapped: 25.4 x 63.5. Pico centred, USB face flush with the -X end.
    # Perf cut to 10 x 21 holes (25.4 x 53.3): the Pico plus one hole row at each end. Pico centred, USB face
    # flush with the -X end. Small parts on the two outer rows; trunk/cord are soldered pigtails (plugs outside
    # the box); the button lives in a lid pocket on two wires. Standoffs: 9 holes from centre, 4.5 rows across.
    "strip": dict(l=53.3, w=25.4, t=1.6, solder_below=1.5, standoff_x=22.86, standoff_u=11.43, SRC="grid"),
    # EEMB 803048 LiPo (measured; datasheet nominal 8.0x30x48)
    "batt": dict(l=50.0, w=30.5, h=8.3, lead_l=8.0, lead_w=8.0, lead_h=5.0,  # lead loop + JST-PH plug off one short end
                 SRC="M"),
    # SunFounder Kepler-kit LiPo charger module (measured). Photo 2026-09-22: JST-PH socket on the -X short end
    # (battery plug axis along X), header pins CLIPPED (wires soldered instead) - pin_below=0.
    "charger": dict(l=19.0, w=8.0, h=7.0, pin_below=0.0, plug_l=9.0, plug_w=5.0, plug_h=5.0, SRC="M/gauge"),   # 8.0: the JST socket overhangs the 6.5 board (gauge 2026-09-22)
    # GY-BNO08X breakout (outline measured; header edge a guess)
    "imu": dict(l=24.0, w=15.3, t=1.2, comp_h=2.3, hdr_pins=8, hdr_pitch=2.54, SRC="gauge"),   # only fit the +1.2 step: ~15.3 wide with headers; caliper tomorrow
    # DFRobot SEN0240: electrode plate AND signal board are both 22x35 (wiki). Thickness/jack unknown.
    "emg_electrode": dict(l=35.0, w=22.0, t=4.0, dot_d=10.0, dot_pitch=10.0, jack_l=12.0, jack_w=6.0, jack_h=5.0,
                          SRC="D/G"),
    "emg_signal": dict(l=35.0, w=22.0, t=4.5, SRC="D/G"),
    # Slide switch (small SS12D00-style, 3 pins). Unverified.
    "switch": dict(l=8.6, w=3.7, h=3.6, nub_l=1.5, nub_w=1.5, nub_h=3.0, travel=2.0, pin_below=3.5,
               pocket_l=9.2, pocket_w=4.3, slot_l=6.0, slot_w=3.0, SRC="gauge"),   # pocket/slot sizes straight from the gauge
    # 12x12 tactile button with square yellow cap (photo 2026-09-22). B3F-4055 style: body 12x12x7.3, legs at 12.5 x 5.0
    "button": dict(l=12.0, w=12.0, h=7.3, cap_l=12.0, cap_w=12.0, cap_h=4.0, cap_r=1.5, cap_hole=12.6,
                   leg_dx=12.5, leg_dy=5.0, leg_below=3.5, SRC="photo/gauge"),   # 12.4 was "best" on the gauge; 12.6 leaves play
    # 5 mm green LED (photo 2026-09-22), 2 legs. Power indicator.
    "led": dict(dome_d=5.0, flange_d=5.8, flange_t=1.0, body_h=8.7, leg_l=6.0, hole=5.0, SRC="photo/gauge"),   # 5.0 printed hole = press fit
    # WS2812B strip segment, 10 mm wide, 60/m (photo). One pixel per 16.67 mm; 5050 LED 1.6 tall on 1.0 mm FPC
    "ws2812": dict(pitch=16.67, w=10.0, t=1.0, led=5.0, led_h=1.6, SRC="photo/D"),
    # 10 mm coin vibration motor (1027 type)
    "motor": dict(d=10.0, h=3.0, lead_l=15.0, cradle_id=10.8, tab_w=4.0, tab_l=3.0, SRC="gauge/photo"),   # side solder tab; fits the 10.8 hole
    # JST-PH 2.0 mm housings (PHR-n): width = (n-1)*2 + 4, mating length 6, height ~4.9
    "jst_ph": dict(pitch=2.0, base_w=4.0, l=6.0, h=4.9, wire_bend=10.0, plug_hole_w2=4.4, plug_hole_w3=6.4, plug_hole_h=5.2,
               socket_w2=6.2, socket_w3=8.2, socket_h=6.0, SRC="gauge"),   # plug openings from the gauge; sockets stay inside
    # Zerone Qi receiver (photo vs tape 2026-09-22): oval coil ~48x35 with a ~20x10 window, black board ~25x15
    # with 2 corner holes, coil leads on one long edge, output wires at a corner; separate ferrite sheet.
    "qi": dict(coil_l=48.0, coil_w=35.0, coil_t=1.0, ferrite_t=0.6, board_l=25.0, board_w=15.0, board_t=2.5,
               SRC="photo"),
    # M2 hardware
    "m2": dict(clear_d=2.3, thread_form_d=2.0, insert_hole_d=3.2, insert_l=4.0, head_d=3.8, SRC="gauge"),   # 2.0 bites by hand; 3.2 holds the insert
}


# --------------------------------------------------------------------------------------------
# Parts. Each returns a build123d Part at origin; keepouts include clearance-independent
# service volumes (plugs, cable bends, travel), NOT print clearance — clr is applied by the caller.
# --------------------------------------------------------------------------------------------
def pico_w(with_headers=True):
    """Pico W, board bottom on Z=0, USB at -X. With headers: black bases + pin stubs hang below Z=0."""
    d = DIM["pico"]
    p = _box(d["l"], d["w"], d["t"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            p -= _cyl(d["hole_d"], 5, sx * d["hole_dx"] / 2, sy * d["hole_dy"] / 2, -1)
    p += _box(d["usb_d"], d["usb_w"], d["usb_h"], -d["l"] / 2 + d["usb_d"] / 2 - d["usb_overhang"], 0, d["t"])
    p += _box(d["shield_l"], d["shield_w"], d["shield_h"], d["l"] / 2 - d["shield_l"] / 2 - 4, 0, d["t"])
    p += _box(d["l"] - 20, d["w"] - 6, d["comp_h"], 2, 0, d["t"])           # generic component height
    if with_headers:
        for sy in (-1, 1):
            y = sy * (d["w"] / 2 - 1.5)  # castellation rows are ~1.5 mm in from the long edges (20 pins each)
            p += _box(20 * d["hdr_pitch"], 2.54, d["hdr_base"], 0, y, -d["hdr_base"])
            p += _box(20 * d["hdr_pitch"], 0.7, d["hdr_pin_below"], 0, y, -d["hdr_base"] - d["hdr_pin_below"])
    return p


def pico_usb_plug():
    """Micro-USB plug seated in the Pico: envelope extending -X from the board end. Position relative to pico_w()."""
    d, u = DIM["pico"], DIM["usb_plug"]
    x0 = -d["l"] / 2 - d["usb_overhang"]                       # connector face
    zc = d["t"] + d["usb_h"] / 2                                # plug centered on the receptacle
    return Box(u["l"], u["w"], u["h"], align=(Align.MAX, Align.CENTER, Align.CENTER)).moved(
        Location((x0 + u["insert"], 0, zc)))


def perf_strip():
    d = DIM["strip"]
    # solder stubs only where the Pico headers are (rows at +-8.9) and the outer part rows
    out = _box(d["l"], d["w"], d["t"])
    for u in (-8.89, 8.89):
        out += _box(d["l"] - 4, 2.6, d["solder_below"], 0, u, -d["solder_below"])
    return out


def pico_on_strip():
    """Pico soldered flat on the perf strip by its headers, USB at the strip's -X end. Strip bottom on Z=0.
    The JST-PH 3-pin cord socket sits in the free rows at the +X end (modelled as a block)."""
    d, s, j = DIM["pico"], DIM["strip"], DIM["jst_ph"]
    z_top = s["t"]
    x_pico = -s["l"] / 2 + d["l"] / 2 + d["usb_overhang"]          # connector face flush with the strip end
    return perf_strip() + pico_w(with_headers=True).moved(Location((x_pico, 0, z_top + d["hdr_base"])))


def battery():
    d = DIM["batt"]
    b = _box(d["l"], d["w"], d["h"])
    return b


def battery_keepout():
    """Cell plus the lead-loop/plug volume off the +X short end."""
    d = DIM["batt"]
    return battery() + _box(d["lead_l"], d["lead_w"], d["lead_h"], d["l"] / 2 + d["lead_l"] / 2, 0, 0)


def charger():
    """SunFounder charger module standing on its long edge is NOT assumed: board flat, pins hang below Z=0."""
    d = DIM["charger"]
    body = _box(d["l"], d["w"], d["h"])
    if d["pin_below"] > 0:
        body += _box(d["l"] - 4, 2.54, d["pin_below"], 0, 0, -d["pin_below"])
    return body


def charger_keepout():
    """Module plus the seated battery plug and its wire bend off the -X short end (photo)."""
    d = DIM["charger"]
    return charger() + _box(d["plug_l"], d["plug_w"], d["plug_h"], -(d["l"] / 2 + d["plug_l"] / 2), 0, 1)


def imu():
    d = DIM["imu"]
    return _box(d["l"], d["w"], d["t"]) + _box(d["l"] - 6, d["w"] - 4, d["comp_h"], 0, 0, d["t"])


def emg_electrode():
    """Dry electrode plate, dots on the -Z face (skin side), 3.5 mm jack body on the +X end (guess)."""
    d = DIM["emg_electrode"]
    return _box(d["l"], d["w"], d["t"]) + _box(d["jack_l"], d["jack_w"], d["jack_h"], d["l"] / 2 - d["jack_l"] / 2, 0, d["t"])


def emg_signal():
    d = DIM["emg_signal"]
    return _box(d["l"], d["w"], d["t"])


def slide_switch():
    """Body on Z=0, nub up (+Z), travel along X, pins hang below."""
    d = DIM["switch"]
    return (_box(d["l"], d["w"], d["h"])
            + _box(d["nub_l"], d["nub_w"], d["nub_h"], 0, 0, d["h"])
            + _box(3 * 2.54, 0.6, d["pin_below"], 0, 0, -d["pin_below"]))


def slide_switch_keepout():
    """Adds the nub's travel and a finger notch above it."""
    d = DIM["switch"]
    return slide_switch() + _box(d["nub_l"] + d["travel"], d["nub_w"], d["nub_h"], 0, 0, d["h"])


def tactile_button():
    """12x12 tactile switch, body bottom on Z=0, square cap on top, 4 legs hanging below (soldered to the strip)."""
    d = DIM["button"]
    b = _box(d["l"], d["w"], d["h"]) + _box(d["cap_l"], d["cap_w"], d["cap_h"], 0, 0, d["h"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            b += _box(0.7, 0.7, d["leg_below"], sx * d["leg_dx"] / 2, sy * d["leg_dy"] / 2, -d["leg_below"])
    return b


def tactile_button_keepout(travel=0.5):
    """Button plus cap travel and a finger-clearance ring around the cap (cut from the lid)."""
    d = DIM["button"]
    return tactile_button() + _box(d["cap_hole"], d["cap_hole"], d["cap_h"] + travel + 3, 0, 0, d["h"])


def led_5mm():
    """Flange on Z=0, dome up, legs down."""
    d = DIM["led"]
    return (_cyl(d["flange_d"], d["flange_t"]) + _cyl(d["dome_d"], d["body_h"] - d["flange_t"], 0, 0, d["flange_t"])
            + _box(2.5, 2.5, d["leg_l"], 0, 0, -d["leg_l"]))


def ws2812_segment(n=2):
    """n-pixel cut of the WS2812B strip, FPC bottom on Z=0, LEDs up, long axis X."""
    d = DIM["ws2812"]
    s = _box(n * d["pitch"], d["w"], d["t"])
    for i in range(n):
        s += _box(d["led"], d["led"], d["led_h"], (i - (n - 1) / 2) * d["pitch"], 0, d["t"])
    return s


def coin_motor():
    d = DIM["motor"]
    return (_cyl(d["d"], d["h"]) + _box(d["tab_l"], d["tab_w"], 1.0, d["d"] / 2 + d["tab_l"] / 2, 0, 0)
            + _box(d["lead_l"], 3, 1.2, d["d"] / 2 + d["tab_l"] + d["lead_l"] / 2, 0, 0))


def jst_ph_plug(n):
    """PHR-n housing, mating face at -X, wire exits +X with a bend keepout."""
    d = DIM["jst_ph"]
    w = d["base_w"] + (n - 1) * d["pitch"]
    return _box(d["l"], w, d["h"]) + _box(d["wire_bend"], w, d["h"], d["l"] / 2 + d["wire_bend"] / 2, 0, 0)


def qi_coil(with_ferrite=True):
    """Oval coil, bottom on Z=0 (ferrite sheet under it, toward the electronics; the coil faces the lid/pad)."""
    d = DIM["qi"]
    t = d["coil_t"] + (d["ferrite_t"] if with_ferrite else 0)
    sk = Rectangle(d["coil_l"], d["coil_w"])
    sk = fillet(sk.vertices(), d["coil_w"] / 2 - 0.01)
    return extrude(sk, amount=t)


def qi_board():
    d = DIM["qi"]
    return _box(d["board_l"], d["board_w"], d["board_t"])


def m2_insert_hole(depth=None):
    d = DIM["m2"]
    return _cyl(d["insert_hole_d"], depth or d["insert_l"] + 1)


PARTS = {
    "pico_w": pico_w, "pico_usb_plug": pico_usb_plug, "perf_strip": perf_strip, "pico_on_strip": pico_on_strip,
    "battery": battery, "battery_keepout": battery_keepout, "charger": charger, "charger_keepout": charger_keepout,
    "imu": imu, "emg_electrode": emg_electrode, "emg_signal": emg_signal, "slide_switch": slide_switch,
    "slide_switch_keepout": slide_switch_keepout, "tactile_button": tactile_button,
    "tactile_button_keepout": tactile_button_keepout, "led_5mm": led_5mm, "ws2812_segment": ws2812_segment,
    "coin_motor": coin_motor, "qi_coil": qi_coil, "qi_board": qi_board,
}


def bbox_str(shape):
    b = shape.bounding_box()
    return f"{b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.1f} mm"
