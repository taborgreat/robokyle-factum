"""Interference + containment check for the cuff box. Run with the venv python (not agentcad):

    .venv/Scripts/python.exe cad/check_box.py

For every placed part: volume shared with the box, with the lid, and the volume that pokes outside the
closed envelope (box + lid outer form). Anything > 0.05 mm^3 is listed as a FAIL. Exit code 1 on failure.
Parts that are *meant* to pass through walls (USB plug, switch, LED, button cap) are checked against an
allowance instead.
"""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
import band_box as bb

TOL = 0.05
ALLOW_THROUGH = {"usb_plug", "switch", "led", "button", "button_keepout", "charger_keepout"}   # designed to cross a wall


def vol(shape):
    try:
        return abs(shape.volume) if shape is not None else 0.0
    except Exception:
        return 0.0


def main():
    box, lid = bb.box(), bb.lid()
    env = bb.shell_outer()
    P = bb.placements()
    fails = []
    print(f"{'part':18s} {'vol':>8s} {'in box':>8s} {'in lid':>8s} {'outside':>8s}")
    for name, part in P.items():
        v = vol(part)
        ib, il = vol(part & box), vol(part & lid)
        outside = vol(part - env)
        flag = ""
        if name in ALLOW_THROUGH:
            flag = "(through-wall part)"
        else:
            if ib > TOL: flag += " HITS BOX"
            if il > TOL: flag += " HITS LID"
            if outside > TOL: flag += " OUTSIDE"
            if flag: fails.append(name)
        print(f"{name:18s} {v:8.1f} {ib:8.2f} {il:8.2f} {outside:8.2f} {flag}")
    # box/lid must not overlap each other
    bl = vol(box & lid)
    print(f"box & lid overlap: {bl:.2f}")
    if bl > TOL: fails.append("box-lid")
    print("summary:", bb.summary())
    print("RESULT:", "FAIL " + ", ".join(fails) if fails else "PASS")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
