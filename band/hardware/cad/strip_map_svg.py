"""Draw the band's perf strip, both sides, from the as-built map (band/PARTS.md "Strip map"). Writes
band/hardware/strip_map.html (inline SVG, no dependencies).  python band/hardware/cad/strip_map_svg.py"""
import io, os, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from band_sections import battery_section, module_section, system_section, EXTRA_CSS
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "band", "hardware", "strip_map.html")

P = 30                   # hole pitch, px
R = 5                    # hole radius
COLS, ROWS = 10, 22
LEFT_PAD, RIGHT_PAD, TOP_PAD, BOT_PAD = 340, 340, 70, 56
W = LEFT_PAD + (COLS - 1) * P + RIGHT_PAD
H = TOP_PAD + (ROWS - 1) * P + BOT_PAD

PIN_L = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7", "GP8", "GP9", "GND", "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"]
PIN_R = ["VBUS", "VSYS", "GND", "3V3_EN", "3V3", "ADC_VREF", "GP28", "GND", "GP27", "GP26", "RUN", "GP22", "GND", "GP21", "GP20", "GP19", "GP18", "GND", "GP17", "GP16"]

# colours by net / destination (token names resolved in CSS)
C = dict(gnd="var(--gnd)", pwr="var(--pwr)", sig="var(--sig)", chg="var(--chg)", sw="var(--sw)", bar="var(--bar)",
         ta="var(--ta)", tb="var(--tb)", cord="var(--cord)", part="var(--part)", led="var(--led)")

# parts on the top: (kind, holes, label, colour)
PARTS = [
    ("led",  [(21, 8), (22, 8)], "LED  + row 21 / − row 22", C["led"]),
    ("res",  [(21, 4), (21, 6)], "470 Ω", C["part"]),
    ("dio",  [(22, 2), (22, 5)], "1N5817 diode 1, stripe at column 2", C["part"]),
    ("res",  [(4, 10), (7, 10)], "R1 100k", C["part"]),
    ("res",  [(7, 10), (10, 10)], "R2 100k", C["part"]),
    ("to92", [(13, 1), (14, 1), (15, 1)], "S8050  E B C (flat face outward)", C["part"]),
    ("res",  [(14, 1), (17, 1)], "1k", C["part"]),
]
# underside solder bridges (runs of adjacent holes)
BRIDGES = [
    ([(21, 6), (21, 7), (21, 8)], "470 → LED +"),
    ([(13, 1), (13, 2)], "E → GND"),
    ([(17, 1), (17, 2)], "1 k → GP13"),
    ([(7, 10), (7, 9)], "divider mid → GP28"),
    ([(5, 9), (5, 10)], "3V3 → 3V3 point"),
]
# underside wires between two stubs: (from, to, label, colour)
UWIRES = [
    ((22, 2), (2, 9), "VSYS  55 mm", C["pwr"]),
    ((22, 5), (4, 10), "divider tap  50 mm", C["sw"]),
    ((10, 10), (8, 9), "divider GND  10 mm", C["gnd"]),
    ((21, 4), (5, 9), "LED supply  45 mm", C["pwr"]),
    ((22, 8), (18, 9), "LED GND  12 mm", C["gnd"]),
]
# leads leaving the board: (stub hole, side 'L'/'R', text, colour)
LEADS = [
    ((3, 2), "L", "charger OUT−  60", C["chg"]),
    ((8, 2), "L", "light bar GND  60  +  trunk A GND  60", C["gnd"]),
    ((1, 2), "L", "cord TX  60", C["cord"]),
    ((2, 2), "L", "cord RX  60", C["cord"]),
    ((18, 2), "L", "cord GND  60", C["cord"]),
    ((6, 2), "L", "trunk B SDA  60", C["tb"]),
    ((7, 2), "L", "trunk B SCL  60", C["tb"]),
    ((9, 2), "L", "trunk B INT  60", C["tb"]),
    ((10, 2), "L", "trunk B BTN  60", C["tb"]),
    ((15, 1), "L", "trunk A MOT−  60  (S8050 C leg)", C["ta"]),
    ((1, 9), "R", "VBUS → 1N5817 → charger IN+  60", C["chg"]),
    ((5, 9), "R", "light bar +5V  60", C["bar"]),
    ((5, 10), "R", "trunk A 3V3 + MOT+  60 each  (3V3 point)", C["ta"]),
    ((9, 9), "R", "trunk A EMG2  60", C["ta"]),
    ((10, 9), "R", "trunk A EMG1  60", C["ta"]),
    ((20, 9), "R", "light bar DIN  60", C["bar"]),
    ((22, 5), "R", "switch outer  60", C["sw"]),
]

def xy(r, c, mirror):
    cc = (COLS + 1 - c) if mirror else c
    return LEFT_PAD + (cc - 1) * P, TOP_PAD + (r - 1) * P

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def board(mirror):
    o = []
    x0, y0 = xy(1, 1, False); x1, y1 = xy(ROWS, COLS, False)
    # board outline
    o.append(f'<rect x="{x0 - 22}" y="{y0 - 20}" width="{x1 - x0 + 44}" height="{y1 - y0 + 40}" rx="4" class="board"/>')
    # USB tab
    ux = (xy(1, 2, mirror)[0] + xy(1, 9, mirror)[0]) / 2
    o.append(f'<rect x="{ux - 17}" y="{y0 - 34}" width="34" height="16" rx="2" class="usb"/><text x="{ux}" y="{y0 - 23}" class="tiny mid">USB</text>')
    # pico footprint
    pxa, pxb = sorted([xy(1, 2, mirror)[0], xy(1, 9, mirror)[0]])
    o.append(f'<rect x="{pxa - 12}" y="{y0 - 12}" width="{pxb - pxa + 24}" height="{19 * P + 24}" rx="5" class="pico"/>')
    o.append(f'<text x="{(pxa + pxb) / 2}" y="{y0 + 9.5 * P}" class="pico-label mid" transform="rotate(-90 {(pxa + pxb) / 2} {y0 + 9.5 * P})">Pico 2 W  ·  {"seen from below" if mirror else "component side up"}</text>')
    # column / row labels
    for c in range(1, COLS + 1):
        x, _ = xy(1, c, mirror)
        o.append(f'<text x="{x}" y="{y0 - 44}" class="lab mid">{c}</text>')
    for r in range(1, ROWS + 1):
        _, y = xy(r, 1, mirror)
        o.append(f'<text x="{x0 - 34}" y="{y + 4}" class="lab end">{r}</text>')
        o.append(f'<text x="{x1 + 34}" y="{y + 4}" class="lab">{r}</text>')
    return o

def holes(mirror, used):
    o = []
    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            x, y = xy(r, c, mirror)
            k = f"h{r}-{c}"
            cls = "hole used" if (r, c) in used else "hole"
            o.append(f'<circle cx="{x}" cy="{y}" r="{R}" class="{cls}"/>')
            # pin names inside the Pico footprint
            name = None
            if 1 <= r <= 20 and c == 2: name = PIN_L[r - 1]
            if 1 <= r <= 20 and c == 9: name = PIN_R[r - 1]
            if name:
                inward = (c == 2) != mirror      # text goes toward the board centre
                tx = x + (10 if inward else -10)
                o.append(f'<text x="{tx}" y="{y + 3.5}" class="pin {"gnd" if name == "GND" else ""} {"" if inward else "end"}">{name}</text>')
            if (r, c) in ((2, 1), (21, 1), (2, 10), (21, 10)):
                o.append(f'<circle cx="{x}" cy="{y}" r="{R + 4}" class="screw"/>')
    return o

def parts(mirror, ghost):
    """Every part with its name and orientation. ghost=True draws it faint on the solder side so you know what sits
    over each blob; mirror flips columns like the board flipped over."""
    o = []; g = " ghost" if ghost else ""
    sgn = -1 if mirror else 1                      # +x is "toward column 10" on the top view, toward column 1 when mirrored
    for kind, hs, label, col in PARTS:
        pts = [xy(r, c, mirror) for r, c in hs]
        if kind == "led":
            (x1, y1), (x2, y2) = pts
            o.append(f'<circle cx="{(x1 + x2) / 2}" cy="{(y1 + y2) / 2}" r="13" class="ledbody{g}"/>')
            o.append(f'<text x="{x1 + 17 * sgn}" y="{y1 + 4}" class="tiny{" end" if mirror else ""}">+ long leg</text>')
            o.append(f'<text x="{x2 + 17 * sgn}" y="{y2 + 4}" class="tiny{" end" if mirror else ""}">− short leg</text>')
            o.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 19}" class="plab mid">green LED</text>')
        elif kind == "res":
            (x1, y1), (x2, y2) = pts
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1)); cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            L = math.hypot(x2 - x1, y2 - y1)
            o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="lead{g}"/>')
            o.append(f'<rect x="{cx - L * 0.28}" y="{cy - 6}" width="{L * 0.56}" height="12" rx="3" class="resbody{g}" transform="rotate({ang} {cx} {cy})"/>')
            if abs(y2 - y1) < 1:
                o.append(f'<text x="{cx}" y="{cy - 12}" class="plab mid">{esc(label)}</text>')
            else:
                lx = cx - 16 if x1 > W / 2 else cx + 16
                o.append(f'<text x="{lx}" y="{cy}" class="plab mid" transform="rotate(-90 {lx} {cy})">{esc(label)}</text>')
        elif kind == "dio":
            (x1, y1), (x2, y2) = pts                                   # hs[0] is the STRIPE end
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2; L = math.hypot(x2 - x1, y2 - y1)
            o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="lead{g}"/>')
            o.append(f'<rect x="{cx - L * 0.3}" y="{cy - 6}" width="{L * 0.6}" height="12" rx="2" class="diobody{g}"/>')
            sx = cx - L * 0.3 + 3 if x1 < x2 else cx + L * 0.3 - 7    # stripe band at the stripe end
            o.append(f'<rect x="{sx}" y="{cy - 6}" width="4" height="12" class="stripe"/>')
            d = -1 if x1 < x2 else 1                                   # current flows plain -> stripe
            ax = cx + d * 0
            o.append(f'<path d="M{cx - 5 * d},{cy - 4} L{cx + 5 * d},{cy} L{cx - 5 * d},{cy + 4} z" class="arrow"/>')
            o.append(f'<text x="{cx}" y="{cy + 20}" class="plab mid">{esc(label)}</text>')
            o.append(f'<text x="{cx}" y="{cy + 31}" class="tiny mid">current → stripe</text>')
        elif kind == "to92":
            (x1, y1), _, (x3, y3) = pts
            h = (y3 - y1) + 24
            # flat face outboard: toward column 1, which is the left edge on top and the right edge underneath
            fx = x1 - 9 * sgn
            o.append(f'<path d="M{fx},{y1 - 12} v{h} a14,{h / 2} 0 0 {1 if mirror else 0} 0,-{h} z" class="to92{g}"/>')
            for (px, py), t in zip(pts, "EBC"):
                o.append(f'<text x="{px - 16 * sgn}" y="{py + 4}" class="tiny{"" if mirror else " end"}">{t}</text>')
            o.append(f'<text x="{x1 + 22 * sgn}" y="{(y1 + y3) / 2}" class="plab mid" transform="rotate(-90 {x1 + 22 * sgn} {(y1 + y3) / 2})">S8050  flat face out</text>')
    return o


def bottom_marks():
    o = []
    for run, label in BRIDGES:
        pts = [xy(r, c, True) for r, c in run]
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        o.append(f'<path d="{d}" class="bridge"/>')
    for a, b, label, col in UWIRES:
        (x1, y1), (x2, y2) = xy(*a, True), xy(*b, True)
        mx, my = (x1 + x2) / 2 + 18, (y1 + y2) / 2
        o.append(f'<path d="M{x1},{y1} Q{mx},{my} {x2},{y2}" class="uwire" style="stroke:{col}"/>')
        o.append(f'<text x="{mx + 4}" y="{my + 3}" class="wlab" style="fill:{col}">{esc(label)}</text>')
    return o

def leads(mirror):
    o = []; slots = {"L": [], "R": []}
    for hole, side, text, col in LEADS:
        s = side if not mirror else ("R" if side == "L" else "L")
        slots[s].append((hole, text, col))
    x0, _ = xy(1, 1, False); x1, _ = xy(1, COLS, False)
    for s, items in slots.items():
        items.sort(key=lambda t: (t[0][0], t[0][1]))
        last_y = -99
        for i, (hole, text, col) in enumerate(items):
            hx, hy = xy(*hole, mirror)
            if hy - last_y < 13: hy = last_y + 13           # two leads on one row: stagger the labels
            last_y = hy
            ex = (x0 - 50) if s == "L" else (x1 + 50)
            lx = (x0 - 58) if s == "L" else (x1 + 58)
            o.append(f'<path d="M{hx},{hy} L{ex},{hy}" class="leadline" style="stroke:{col}"/>')
            o.append(f'<circle cx="{ex}" cy="{hy}" r="3" style="fill:{col}"/>')
            o.append(f'<text x="{lx}" y="{hy + 4}" class="wlab {"end" if s == "L" else ""}" style="fill:{col}">{esc(text)}</text>')
    return o

def svg(mirror, title):
    used = set()
    for _, hs, _, _ in PARTS: used.update(hs)
    for run, _ in BRIDGES: used.update(run)
    for a, b, _, _ in UWIRES: used.update([a, b])
    for hole, *_ in LEADS: used.add(hole)
    for r in range(1, 21): used.update([(r, 2), (r, 9)])
    body = board(mirror) + holes(mirror, used) + (bottom_marks() if mirror else []) + parts(mirror, ghost=mirror) + leads(mirror)
    return (f'<figure><figcaption>{title}</figcaption><svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">'
            + "\n".join(body) + "</svg></figure>")

CSS = """
:root{--bg:#f6f4ef;--ink:#1d1f24;--mute:#6b6f7a;--line:#cfcac0;--board:#e9dfc7;--pico:#d7e6d6;--hole:#fff;--hole-line:#8a8478;
--used:#3b3f4a;--gnd:#222;--pwr:#c0392b;--sig:#1f5fbf;--chg:#7d3c98;--sw:#1d6fa5;--bar:#0f7f7a;--ta:#2e7d32;--tb:#b26a00;--cord:#5d6d7e;--part:#4a4a4a;--led:#2e9e44;--screw:#b03a2e}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171b;--ink:#e8e6e1;--mute:#9a9ea8;--line:#3a3d45;--board:#3d3524;--pico:#233127;--hole:#0e0f12;--hole-line:#7a7468;
--used:#e8e6e1;--gnd:#e8e6e1;--pwr:#ff6b5b;--sig:#6fa6ff;--chg:#c58ee0;--sw:#5fb3ec;--bar:#3fd0c9;--ta:#6fcf74;--tb:#f0a93a;--cord:#aab7c4;--part:#d0d0d0;--led:#5fd67a;--screw:#ff7b6b}}
:root[data-theme=dark]{--bg:#15171b;--ink:#e8e6e1;--mute:#9a9ea8;--line:#3a3d45;--board:#3d3524;--pico:#233127;--hole:#0e0f12;--hole-line:#7a7468;
--used:#e8e6e1;--gnd:#e8e6e1;--pwr:#ff6b5b;--sig:#6fa6ff;--chg:#c58ee0;--sw:#5fb3ec;--bar:#3fd0c9;--ta:#6fcf74;--tb:#f0a93a;--cord:#aab7c4;--part:#d0d0d0;--led:#5fd67a;--screw:#ff7b6b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 "IBM Plex Sans",system-ui,sans-serif;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.01em}h2{font-size:18px;margin:28px 0 4px}h3{font-size:15px;margin:16px 0 4px}ol{margin:4px 0 0;padding-left:22px}ol li{margin:3px 0}ul{margin:2px 0 0;padding-left:18px}p.sub{color:var(--mute);margin:0 0 20px;max-width:70ch}
.wrap{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start}figure{margin:0;flex:1 1 520px;min-width:0}
figcaption{font-weight:600;margin:0 0 6px}svg{width:100%;height:auto;display:block;background:transparent}
.board{fill:var(--board);stroke:var(--line)}.usb{fill:var(--mute)}.pico{fill:var(--pico);stroke:var(--line)}
.hole{fill:var(--hole);stroke:var(--hole-line);stroke-width:1}.hole.used{fill:var(--used)}
.screw{fill:none;stroke:var(--screw);stroke-width:1.5;stroke-dasharray:3 2}
text{font-family:"IBM Plex Mono",ui-monospace,monospace;fill:var(--ink)}.lab{font-size:11px;fill:var(--mute)}.mid{text-anchor:middle}.end{text-anchor:end}
.pin{font-size:9.5px}.pin.gnd{fill:var(--mute)}.tiny{font-size:10px}.pico-label{font-size:11px;fill:var(--mute);letter-spacing:.06em}
.lead{stroke:var(--part);stroke-width:2}.resbody{fill:#d9b56a;stroke:var(--part)}.diobody{fill:#333;stroke:var(--part)}.stripe{fill:#ddd}
.ledbody{fill:var(--led);opacity:.85}.ghost{opacity:.32;stroke-dasharray:3 2}.arrow{fill:#fff}.plab{font-size:10px;fill:var(--ink);font-weight:500}.to92{fill:#333;stroke:var(--part)}
.bridge{stroke:var(--used);stroke-width:9;stroke-linecap:round;fill:none;opacity:.85}
.uwire{fill:none;stroke-width:2.2;stroke-linecap:round}.wlab{font-size:10.5px}.leadline{stroke-width:2;fill:none;stroke-dasharray:4 3}
.legend{display:flex;flex-wrap:wrap;gap:10px 18px;margin:18px 0 0;padding:0;list-style:none;font-size:13px}
.legend li::before{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-2px;background:var(--c)}
table{border-collapse:collapse;margin-top:22px;font-size:13px}td,th{text-align:left;padding:4px 10px;border-bottom:1px solid var(--line)}th{font-weight:600}
"""

PART_STEPS = [
    ("Pico", "rows 1–20, columns 2 and 9, USB face flush with the row-1 edge. Tack two diagonal pins, check it sits flat and square, solder the other 38, clip all to 1.5 mm. Plug USB in and run the blink before anything else goes on."),
    ("green LED", "long leg (21,8), short leg (22,8). Hold the flange 1 mm above the board while soldering. Clip."),
    ("470 Ω", "flat on row 21, legs (21,4) and (21,6). Solder, clip."),
    ("1N5817 diode 1", "flat on row 22, STRIPE end (22,2), plain end (22,5). Solder, clip."),
    ("R1 100k", "flat on column 10, legs (4,10) and (7,10). Solder (4,10) only for now, clip it."),
    ("R2 100k", "flat on column 10, legs (7,10) and (10,10). Its top leg goes into (7,10) WITH R1's leg: twist the two together first. Solder (7,10) and (10,10), clip."),
    ("S8050", "standing on column 1, legs E (13,1), B (14,1), C (15,1), flat face away from the Pico, E nearest the USB end. Solder, clip."),
    ("1 kΩ", "one lead soldered to the transistor's B leg 3 mm above the board (a top-side joint), body lying toward the far end on the outer side of the C leg, other lead into (17,1). Solder (17,1), clip."),
]
CHECKS = [
    "LED: diode mode, red on (21,8) stub, black on (22,8) stub: ~2 V and a faint glow. Open = LED backwards.",
    "470 Ω: ohms, (21,4) stub to (21,8) stub: 470. Open = the (21,6)–(21,8) run is incomplete.",
    "(22,8) must not touch (21,8): diode mode both ways between them reads open in one direction, not a short.",
    "Diode 1: diode mode, red on (22,5) stub, black on (22,2) stub: ~0.2 V. Swapped = diode in backwards.",
    "Divider: ohms (4,10) to (10,10): 200 k; (7,9) to either end: 100 k.",
    "S8050: diode mode, red on B (14,1): ~0.6 V to E and to C. Open both = legs swapped.",
    "No bridge (13,1)/(13,2) to (14,1): ohms B to GND reads open (not the 1 k).",
    "GND to 3V3 (any GND stub to (5,9)): must not beep.",
]

def build_list():
    o = ['<h3>Build order</h3><p class="sub">Everything in the drawing, in the order to do it. Parts from the top, all solder underneath, leads clipped to 1.5 mm. Wires are tinned and laid along a stub, one joint each.</p>']
    o.append("<h3>1. Parts</h3><ol>")
    for name, how in PART_STEPS: o.append(f"<li><strong>{esc(name)}</strong>: {esc(how)}</li>")
    o.append("</ol><h3>2. Solder bridges underneath</h3><ol>")
    for run, label in BRIDGES:
        o.append(f"<li>{esc(label)}: one run of solder across " + " – ".join(f"({r},{c})" for r, c in run) + "</li>")
    o.append("</ol><h3>3. Wires that stay under the board</h3><ol>")
    for a, b, label, col in UWIRES:
        o.append(f"<li>{esc(label)}: from the stub at ({a[0]},{a[1]}) to the stub at ({b[0]},{b[1]}), routed in the bare lanes, never over another stub.</li>")
    o.append("</ol><h3>4. Leads leaving the board (tin, lay along the stub, one joint)</h3><ol>")
    groups = [("charger", C["chg"]), ("switch", C["sw"]), ("light bar", C["bar"]), ("trunk A", C["ta"]), ("trunk B", C["tb"]), ("cord", C["cord"]), ("VBUS", C["chg"])]
    for gname, gcol in groups:
        items = [(h, t) for h, side, t, col in LEADS if t.lower().startswith(gname.lower())]
        if not items: continue
        o.append(f'<li><strong>{esc(gname)}</strong><ul>')
        for (r, c), t in items:
            o.append(f"<li>{esc(t)} → stub at ({r},{c})</li>")
        if gname == "charger": o.append("<li>charger OUT+  60 → the switch's middle pin (not the strip)</li>")
        if gname == "VBUS": o.append("<li>the 1N5817 sits in this wire, stripe toward the charger; heat-shrink over it</li>")
        o.append("</ul></li>")
    o.append("</ol><p class=\"sub\">Stubs that take two wires: (5,9) 3V3 takes the LED supply and the light bar +5V; (8,2) GND takes the light bar GND and trunk A GND; (5,10) takes trunk A 3V3 and MOT+. Tin both ends together, then one joint.</p>")
    o.append("<h3>5. Meter checks before it goes in the box</h3><ol>")
    for c in CHECKS: o.append(f"<li>{esc(c)}</li>")
    o.append("</ol><p class=\"sub\">Then Kapton over the solder side (standoff holes clear), and the bench script once more with everything dangling.</p>")
    return "\n".join(o)


def page():
    legend = [("solder blob / used hole", "--used"), ("ground", "--gnd"), ("battery / 3V3", "--pwr"), ("charger", "--chg"), ("switch, divider tap", "--sw"),
              ("light bar", "--bar"), ("trunk A", "--ta"), ("trunk B", "--tb"), ("hand cord", "--cord"), ("standoff screw", "--screw")]
    li = "".join(f'<li style="--c:var({v})">{esc(k)}</li>' for k, v in legend)
    rows = [
        ("Pico", "rows 1–20, columns 2 and 9", "USB face flush with the row-1 edge"),
        ("green LED", "+ long leg (21,8), − short leg (22,8)", "flange 1 mm above the board; long leg = anode = toward the 470 Ω"),
        ("470 Ω", "(21,4) → (21,6)", "underside solder run (21,6)–(21,7)–(21,8)"),
        ("1N5817 diode 1", "stripe (22,2), plain (22,5)", "stripe toward column 1 / the middle wall; current flows from the switch side into VSYS"),
        ("R1 / R2 100 k", "(4,10)→(7,10), (7,10)→(10,10)", "shared hole (7,10); bridge (7,10)–(7,9) = GP28"),
        ("S8050", "E (13,1) B (14,1) C (15,1)", "standing; flat face toward the board edge (away from the Pico); E nearest the USB end; bridge (13,1)–(13,2) = GND"),
        ("1 kΩ", "B leg → (17,1)", "bridge (17,1)–(17,2) = GP13"),
        ("3V3 point", "bridge (5,9)–(5,10)", "trunk A 3V3 lands on (5,10)"),
    ]
    tr = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in rows)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Band Build Maps</title><link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{CSS}{EXTRA_CSS}</style></head><body>
<h1>Band build maps</h1><p class="sub">Four separate sections: the strip (both sides), the battery bay, the forearm module, and the whole band with its cables. Each has its own diagram and its own build order; nothing in one section refers to holes in another.</p><section id="strip"><h2>1. The strip, both sides</h2>
<p class="sub">Look down at the top with the USB end at the top: column 1 top-left, column 10 top-right, rows 1–22 from the USB end. Pin 1 (GP0) is at (1,2), pin 40 (VBUS) at (1,9). The bottom view is the board flipped left-to-right, USB still at the top, so column 1 appears on the right. Dark holes carry solder. Lengths in mm.</p>
<div class="wrap">{svg(False, "TOP — components (nothing else is soldered here)")}{svg(True, "BOTTOM — solder side, board flipped over (bridges, underside wires, leads leaving)")}</div>
<ul class="legend">{li}</ul>
<table><thead><tr><th>part</th><th>holes</th><th>note</th></tr></thead><tbody>{tr}</tbody></table>
{build_list()}
</section>{battery_section()}{module_section()}{system_section()}<p class="sub" style="margin-top:18px">The slide switch is not on the strip: it is glued between the two fins on the chest wall (right-hand side here, beside rows 12–17) and reaches the board only through its two wires, charger OUT+ into its middle pin and its outer pin down to diode 1 at (22,5). Every hole in columns 1 and 10 has a Pico pin 2.5 mm away: keep those joints small. Column 10 above row 10 stays empty (switch fins rows 12–17, LED hole). Underside wires cross in the bare lanes under the Pico, never over a stub. Source of truth: band/PARTS.md, “Strip map”.</p>
</body></html>"""

io.open(OUT, "w", encoding="utf-8").write(page())
print("wrote", OUT)
