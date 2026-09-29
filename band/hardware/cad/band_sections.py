"""Extra sections for the viewer's Build tab (band/viewer/index.html): the battery bay, the forearm module and the whole
band with its cables. Port-to-port block diagrams (not to scale) plus a build order for each. Imported by strip_map_svg.py."""
import math

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

class Sch:
    """Tiny schematic helper: rectangles with named ports, orthogonal wires between ports."""
    def __init__(self, w, h): self.w, self.h, self.o, self.ports = w, h, [], {}
    def node(self, key, x, y, w, h, title, ports, cls="node", sub=""):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{cls}"/>')
        self.o.append(f'<text x="{x + w / 2}" y="{y + 16}" class="ntitle mid">{esc(title)}</text>')
        if sub: self.o.append(f'<text x="{x + w / 2}" y="{y + 29}" class="nsub mid">{esc(sub)}</text>')
        for name, side, f in ports:
            if side == "l": px, py, tx, anc = x, y + h * f, x + 6, ""
            elif side == "r": px, py, tx, anc = x + w, y + h * f, x + w - 6, " end"
            elif side == "t": px, py, tx, anc = x + w * f, y, x + w * f, " mid"
            else: px, py, tx, anc = x + w * f, y + h, x + w * f, " mid"
            self.ports[(key, name)] = (px, py)
            self.o.append(f'<circle cx="{px}" cy="{py}" r="3.2" class="port"/>')
            ty = py + 4 if side in "lr" else (y + 12 if side == "t" else y + h - 5)
            self.o.append(f'<text x="{tx}" y="{ty}" class="pname{anc}">{esc(name)}</text>')
    def wire(self, a, b, label="", col="var(--ink)", bend=None, lab_dy=-5, lab_dx=0):
        (x1, y1), (x2, y2) = self.ports[a], self.ports[b]
        mx = bend if bend is not None else (x1 + x2) / 2
        d = f"M{x1},{y1} L{mx},{y1} L{mx},{y2} L{x2},{y2}"
        self.o.append(f'<path d="{d}" class="swire" style="stroke:{col}"/>')
        if label: self.o.append(f'<text x="{mx + lab_dx}" y="{(y1 + y2) / 2 + lab_dy}" class="wlab mid" style="fill:{col}">{esc(label)}</text>')
    def diode(self, a, b, label, col, bend=None, lab_dy=-8):
        """wire a -> b with a diode symbol at the bend, current a -> b (stripe at the b side)"""
        (x1, y1), (x2, y2) = self.ports[a], self.ports[b]
        mx = bend if bend is not None else (x1 + x2) / 2
        self.o.append(f'<path d="M{x1},{y1} L{mx},{y1} L{mx},{y2} L{x2},{y2}" class="swire" style="stroke:{col}"/>')
        cy = (y1 + y2) / 2; up = 1 if y2 > y1 else -1
        self.o.append(f'<rect x="{mx - 7}" y="{cy - 9}" width="14" height="18" class="diobody"/>')
        self.o.append(f'<rect x="{mx - 7}" y="{cy + (5 if up > 0 else -9)}" width="14" height="4" class="stripe"/>')
        self.o.append(f'<path d="M{mx - 4},{cy - 4 * up} L{mx + 4},{cy - 4 * up} L{mx},{cy + 3 * up} z" class="arrow"/>')
        self.o.append(f'<text x="{mx + 11}" y="{cy + 4}" class="wlab" style="fill:{col}">{esc(label)}</text>')
    def text(self, x, y, t, cls="note"): self.o.append(f'<text x="{x}" y="{y}" class="{cls}">{esc(t)}</text>')
    def svg(self, title):
        return (f'<figure><figcaption>{esc(title)}</figcaption><svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(title)}">'
                + "\n".join(self.o) + "</svg></figure>")

C = dict(gnd="var(--gnd)", pwr="var(--pwr)", sig="var(--sig)", chg="var(--chg)", sw="var(--sw)", bar="var(--bar)",
         ta="var(--ta)", tb="var(--tb)", cord="var(--cord)", led="var(--led)")

def ol(items): return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"

# ------------------------------------------------------------------ battery bay
def battery_section():
    s = Sch(960, 470)
    s.node("cell", 20, 150, 130, 80, "LiPo cell", [("red +", "r", 0.35), ("black −", "r", 0.7)], sub="EEMB 1200 mAh")
    s.node("pig", 200, 150, 90, 80, "PH2 pigtail", [("in +", "l", 0.35), ("in −", "l", 0.7), ("B+", "r", 0.35), ("B−", "r", 0.7)], cls="node small", sub="header + 30 mm")
    s.node("chg", 360, 110, 190, 190, "Charger board", [("B+", "l", 0.25), ("B−", "l", 0.4), ("IN+", "l", 0.7), ("IN−", "l", 0.85), ("OUT+", "r", 0.25), ("OUT−", "r", 0.5)], sub="AITRIP TP4057, protection on OUT−")
    s.node("sw", 640, 60, 130, 70, "Slide switch", [("middle", "l", 0.5), ("outer A", "r", 0.35), ("outer B", "r", 0.7)], sub="on its chest-wall shelf past the strip's end")
    s.node("strip", 820, 40, 120, 250, "Strip", [("(22,5) D1 plain", "l", 0.2), ("(3,2) GND", "l", 0.5), ("(1,9) VBUS", "l", 0.8)], sub="see the map above")
    s.node("qi", 360, 360, 190, 80, "Qi receiver board", [("out +", "r", 0.35), ("out −", "r", 0.7), ("coil", "l", 0.5)], sub="on the cradle's bracket tops")
    s.node("coil", 60, 360, 200, 80, "Qi coil + ferrite", [("leads", "r", 0.5)], sub="on the cell, ferrite DOWN, Kapton band")
    s.wire(("cell", "red +"), ("pig", "in +"), "", C["pwr"]); s.wire(("cell", "black −"), ("pig", "in −"), "", C["gnd"])
    s.wire(("pig", "B+"), ("chg", "B+"), "", C["pwr"]); s.wire(("pig", "B−"), ("chg", "B−"), "", C["gnd"])
    s.wire(("chg", "OUT+"), ("sw", "middle"), "110 mm", C["sw"], bend=600)
    s.wire(("sw", "outer A"), ("strip", "(22,5) D1 plain"), "30 mm", C["sw"], bend=795)
    s.wire(("chg", "OUT−"), ("strip", "(3,2) GND"), "60 mm, ground", C["gnd"], bend=700, lab_dy=-6)
    s.wire(("coil", "leads"), ("qi", "coil"), "", C["bar"])
    s.diode(("qi", "out +"), ("chg", "IN+"), "diode 2, 1N5817", C["bar"], bend=600)
    s.wire(("qi", "out −"), ("chg", "IN−"), "", C["bar"], bend=620)
    s.diode(("strip", "(1,9) VBUS"), ("chg", "IN+"), "diode 3, 1N5817", C["chg"], bend=740)
    s.text(20, 30, "Cell → charger → switch → strip.  IN+ has two diode feeds (pad and USB); the switch alone owns the battery.", "note")
    steps = [
        "<strong>Pigtail</strong>: 2-pin PH header, red 30 mm to B+, black 30 mm to B−, wires in from the top, soldered underneath. Meter the cell's plug to find plus before the first plug-in; red must land on B+.",
        "<strong>Charger leads</strong>, 60 mm, from the top, soldered underneath: OUT+, OUT−, IN+, IN−. Leave the board's own USB-C empty.",
        "<strong>Qi receiver</strong>: splice diode 2 into its + output wire, stripe toward the charger, heat-shrink; + → IN+, − → IN−. Coil: ferrite sheet on the side that faces the cell.",
        "<strong>Diode 3</strong> in the strip's VBUS lead (from stub (1,9)), stripe toward the charger, joins IN+ with diode 2's wire: twist, tin, one joint on the IN+ pad.",
        "<strong>Switch</strong>: OUT+ to its middle pin (110 mm: through the USB-end notch, along the strip's middle-wall edge, past row 22); its outer pin to the strip's diode 1 plain stub (22,5), 30 mm; the second outer pin stays empty.",
        "<strong>Bench proof before the box</strong> (BENCH stage 1 + 3): OUT+ to OUT− reads the cell; IN− ↔ OUT− beeps, B− ↔ OUT− does not; switch off + coil on the pad = red LED, Pico dark; switch on = Pico runs; USB in = Pico runs and red LED.",
        "<strong>Into the box, in this order</strong>: box onto the plate (2 × M2×6 from inside) → trunk A header into the battery-bay end-wall pocket, leads behind the ring → charger into its cradle, USB-C toward the triceps wall, pads toward the middle wall, cell leads back through the ring's notch → Kapton over it → Qi board on the four bracket tops → cell into the ring, lip toward the charger → ferrite + coil on the cell, Kapton band → strip-side headers → strip → switch onto its shelf → light bar → lid.",
    ]
    return ('<section id="battery"><h2>2. Battery bay: cell, charger, switch, Qi</h2>'
            '<p class="sub">Port to port. Nothing here touches the strip except three wires: the switch return into (22,5), ground into (3,2), and the VBUS lead out of (1,9).</p>'
            + s.svg("Battery bay wiring (block diagram, not to scale)") + "<h3>Build order</h3>" + ol(steps) + "</section>")

# ------------------------------------------------------------------ forearm module
def module_section():
    s = Sch(960, 620)
    s.node("ph6", 20, 60, 150, 250, "PH6 trunk A", [("1  3V3", "r", 0.12), ("2  GND", "r", 0.27), ("3  EMG1", "r", 0.42), ("4  EMG2", "r", 0.57), ("5  MOT+", "r", 0.72), ("6  MOT−", "r", 0.87)], sub="lower in the elbow pocket")
    s.node("ph4", 20, 340, 150, 180, "PH4 trunk B", [("1  SDA", "r", 0.18), ("2  SCL", "r", 0.4), ("3  INT", "r", 0.62), ("4  BTN", "r", 0.84)], sub="stacked on top of the PH6")
    s.node("bA", 420, 40, 210, 110, "Board A  (flexor)", [("−", "l", 0.3), ("+", "l", 0.55), ("S", "l", 0.8), ("jack", "r", 0.5)], sub="bay A, M3×5 ×2; wires cross the rib passage")
    s.node("bB", 420, 170, 210, 110, "Board B  (extensor)", [("−", "l", 0.3), ("+", "l", 0.55), ("S", "l", 0.8), ("jack", "r", 0.5)], sub="bay B over the IMU, M3×6 ×2")
    s.node("imu", 420, 310, 210, 150, "BNO08x IMU", [("VCC", "l", 0.14), ("GND", "l", 0.3), ("SDA", "l", 0.46), ("SCL", "l", 0.6), ("INT", "l", 0.74)], sub="under board B, M2×4 ×2; PS0 PS1 AD0 → GND, RST → VCC, CS open")
    s.node("btn", 420, 490, 120, 60, "Button", [("leg", "l", 0.35), ("leg (diagonal)", "l", 0.72)], cls="node small", sub="in the rib, cap up")
    s.node("mot", 560, 490, 120, 60, "Coin motor", [("lead", "l", 0.35), ("lead", "l", 0.72)], cls="node small", sub="blind pocket; 1N4007 across its tabs, stripe on MOT+")
    s.node("fA", 760, 40, 180, 110, "Flexor frame", [("3.5 mm", "l", 0.5)], sub="inside of forearm")
    s.node("fB", 760, 170, 180, 110, "Extensor frame", [("3.5 mm", "l", 0.5)], sub="outside of forearm")
    # power fan-out
    s.wire(("ph6", "1  3V3"), ("bA", "+"), "", C["pwr"], bend=230); s.wire(("ph6", "1  3V3"), ("bB", "+"), "", C["pwr"], bend=230)
    s.wire(("ph6", "1  3V3"), ("imu", "VCC"), "3V3: three wires on pin 1", C["pwr"], bend=230, lab_dy=-70, lab_dx=60)
    s.wire(("ph6", "2  GND"), ("bA", "−"), "", C["gnd"], bend=260); s.wire(("ph6", "2  GND"), ("bB", "−"), "", C["gnd"], bend=260)
    s.wire(("ph6", "2  GND"), ("imu", "GND"), "GND: four wires on pin 2", C["gnd"], bend=260, lab_dy=-40, lab_dx=70)
    s.wire(("ph6", "2  GND"), ("btn", "leg (diagonal)"), "", C["gnd"], bend=260)
    s.wire(("ph6", "3  EMG1"), ("bA", "S"), "EMG1", C["ta"], bend=300)
    s.wire(("ph6", "4  EMG2"), ("bB", "S"), "EMG2", C["ta"], bend=320)
    s.wire(("ph6", "5  MOT+"), ("mot", "lead"), "MOT+ (motor supply, its own wire)", C["ta"], bend=340, lab_dy=-6)
    s.wire(("ph6", "6  MOT−"), ("mot", "lead"), "MOT− (to the collector)", C["ta"], bend=360, lab_dy=8)
    for p, q in (("1  SDA", "SDA"), ("2  SCL", "SCL"), ("3  INT", "INT")):
        s.wire(("ph4", p), ("imu", q), "", C["tb"], bend=380)
    s.wire(("ph4", "4  BTN"), ("btn", "leg"), "BTN", C["tb"], bend=400)
    s.wire(("bA", "jack"), ("fA", "3.5 mm"), "plate cable", C["cord"], bend=700)
    s.wire(("bB", "jack"), ("fB", "3.5 mm"), "plate cable", C["cord"], bend=700)
    s.text(200, 582, "All wires 60 mm: under the boards at the Gravity pins, onto the headers' clipped pins.", "note")
    s.text(200, 598, "The motor has its own pair, MOT+ and MOT−, so its current never rides the boards' 3V3 or GND.", "note")
    steps = [
        "<strong>IMU</strong>: clip its header to ~2 mm; one short jumper joins PS0, PS1 and AD0 to the board's own GND pin (I²C mode, address 0x4A; the firmware probes both), another joins RST to VCC; leave CS open. Five 60 mm wires on VCC, GND, SDA, SCL, INT. Screw it to its two posts in bay B, header edge toward the rib, 2 × M2×4.",
        "<strong>Headers</strong>: clip the PH6's and PH4's pins to 2 mm, solder a 60 mm lead on every pin, drop both into the elbow-wall pocket, PH6 below (trunk A), PH4 above (trunk B), hot glue on top. Pin 1 is the end with the housing's ramp.",
        "<strong>Motor</strong>: solder the 1N4007 across its two tabs first, standing up along the tab slot, stripe on the tab that will be MOT+ (PH6 pin 5); the other tab is MOT− (PH6 pin 6). Leads up the tab slot into the rib tunnel and out the wall hole into bay B; peel the pad, press it onto the pocket floor, tab toward the button.",
        "<strong>Button</strong>: clip two legs flush and the other two to 1.5 mm; two wires soldered sideways (one leg → PH4 pin 4, the diagonal leg → PH6 pin 2); down the tunnel with the motor leads; drop it in its pocket cap up.",
        "<strong>Board A</strong> (flexor, EMG1): three wires on its Gravity pins under the board (− → PH6 2, + → PH6 1, S → PH6 3), pass them through the rib passage into bay B, screw the board to its posts, jack end to the wrist wall, 2 × M3×5.",
        "<strong>Board B</strong> (extensor, EMG2): same, − → PH6 2, + → PH6 1, S → PH6 4; it sits over the IMU on the tall posts, 2 × M3×6.",
        "<strong>Header pins with many wires</strong>: PH6 pin 1 takes three (board A +, board B +, IMU VCC), pin 2 takes four (board A −, board B −, IMU GND, button). Twist and tin each group, then one joint on the pin.",
        "<strong>Close</strong>: backer under the strap with the strap between its rails, module on top, 2 × M2×8 from the skin side into the inserts under the crest bosses (pan heads), lid on, 4 × M2×6 (crest and side ears). Bench: plug the trunk into the box, run the stage-4 script; IMU ok and both EMG columns move.",
        "<strong>Electrode frames</strong>: plate into the frame bars down, loop band down through one cover slot and up the other, cover on, 4 × M2×6; 3.5 mm cable to the matching jack (flexor → board A, extensor → board B).",
    ]
    return ('<section id="module"><h2>3. Forearm module: boards, IMU, button, motor, trunk headers</h2>'
            '<p class="sub">Port to port. Everything inside the module ends on the two stacked headers; the trunk cables carry it to the box.</p>'
            + s.svg("Forearm module wiring (block diagram, not to scale)") + "<h3>Build order</h3>" + ol(steps) + "</section>")

# ------------------------------------------------------------------ the whole band
def system_section():
    s = Sch(960, 330)
    s.node("box", 20, 60, 260, 200, "Band box  (upper arm)", [("PH6 trunk A", "r", 0.25), ("PH4 trunk B", "r", 0.5), ("PH3 hand cord", "r", 0.75), ("micro-USB", "l", 0.3), ("Qi coil under the lid", "l", 0.7)], sub="Pico 2 W, cell, charger, switch")
    s.node("mod", 430, 40, 250, 150, "Forearm module  (thumb side, 1.5\" strap)", [("PH6 + PH4 stacked", "l", 0.4), ("jack A", "r", 0.35), ("jack B", "r", 0.65)], sub="2 signal boards, IMU, button, motor")
    s.node("fA", 800, 30, 150, 70, "Flexor frame", [("3.5 mm", "l", 0.5)], cls="node small", sub="inside of the forearm")
    s.node("fB", 800, 120, 150, 70, "Extensor frame", [("3.5 mm", "l", 0.5)], cls="node small", sub="outside of the forearm")
    s.node("claw", 430, 230, 250, 70, "Claw  (coming soon)", [("PH3", "l", 0.5)], cls="node dashed", sub="Pico W, servo gripper; own battery")
    s.wire(("box", "PH6 trunk A"), ("mod", "PH6 + PH4 stacked"), "trunk A, PH6 ↔ PH6, 25 cm", C["ta"], bend=340, lab_dy=-10)
    s.wire(("box", "PH4 trunk B"), ("mod", "PH6 + PH4 stacked"), "trunk B, PH4 ↔ PH4, 25 cm (glued to trunk A at the module end)", C["tb"], bend=370, lab_dy=14)
    s.wire(("box", "PH3 hand cord"), ("claw", "PH3"), "hand cord, PH3 ↔ PH3, TX/RX crossed, length as needed", C["cord"], bend=360, lab_dy=-8)
    s.wire(("mod", "jack A"), ("fA", "3.5 mm"), "3.5 mm, the kit's", C["cord"], bend=740)
    s.wire(("mod", "jack B"), ("fB", "3.5 mm"), "3.5 mm, the kit's", C["cord"], bend=740)
    s.text(30, 292, "Plug-to-plug everywhere: headers (pins) in the walls, crimped housings on the cables.", "note")
    s.text(30, 308, "Twist EMG1, EMG2 and GND together in trunk A; braided sleeving over both trunks.", "note")
    steps = [
        "<strong>Trunk A</strong>: PH6 housing at both ends, six wires 25 cm, order 3V3 GND EMG1 EMG2 MOT+ MOT− pin 1 to 6 at both ends (straight through). Twist EMG1, EMG2 and GND together along the run; twist MOT+ with MOT−.",
        "<strong>Trunk B</strong>: PH4 both ends, SDA SCL INT BTN straight through, 25 cm. Glue its module-end housing face-to-face with trunk A's after a first plug-in so the pair sits square in the stacked pocket.",
        "<strong>Hand cord</strong>: PH3 both ends, TX RX GND, <em>crossed</em> (band TX → hand RX). Make it when the claw is ready.",
        "<strong>Plate cables</strong>: the kit's 3.5 mm leads, flexor plate → jack A, extensor plate → jack B.",
        "Crimp recipe (PA-09): strip 2.5 mm, no tinning, conductor in the 1.4 slot, insulation in the 1.9 slot, tug test, contact in with its lance toward the housing windows until it clicks. Thin wire: double the copper over, heat-shrink under the insulation tabs.",
    ]
    return ('<section id="system"><h2>4. The whole band and its cables</h2>'
            '<p class="sub">Where each box sits and which plug joins them. The band never receives commands; the cables carry power and signals out to the forearm, and serial to the hand.</p>'
            + s.svg("Band, forearm module, electrode frames, claw: connectors and cables") + "<h3>Cables to make</h3>" + ol(steps) + "</section>")

EXTRA_CSS = """
.build section{margin-top:44px;padding-top:24px;border-top:2px solid var(--line)}
.build .node{fill:var(--pico);stroke:var(--line);stroke-width:1.2}.build .node.small{fill:var(--board)}.build .node.dashed{fill:none;stroke-dasharray:6 4}
.build .ntitle{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:13px;font-weight:600}.build .nsub{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:10.5px;fill:var(--mute)}
.build .port{fill:var(--bg);stroke:var(--ink);stroke-width:1.4}.build .pname{font-size:10px}.build .swire{fill:none;stroke-width:2;stroke-linejoin:round}.build .note{font-size:11px;fill:var(--mute);font-family:"IBM Plex Sans",system-ui,sans-serif}
"""
