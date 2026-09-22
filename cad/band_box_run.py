# agentcad run cad/band_box_run.py --label box --params PART=box   (PART: all | box | lid | parts)
import band_box as bb
PART = "all"

import sys; print(bb.summary(), file=sys.stderr)
if PART in ("all", "box"):
    show_object(bb.box(), id="box", name="cuff box")
if PART in ("all", "lid"):
    show_object(bb.lid(), id="lid", name="lid")
if PART in ("all", "parts"):
    for k, v in bb.placements().items():
        if not k.endswith("keepout") and k != "usb_plug":
            show_object(v, id=k, name=k)
