# agentcad run band/hardware/cad/forearm_run.py --label fa_module --params PART=module
# PART: all | module | lid | backer | frame | cover | parts | eparts
import forearm as fa
PART = "all"

import sys; print(fa.summary(), file=sys.stderr)
if PART in ("all", "module"):
    show_object(fa.module(), id="module", name="forearm module")
if PART in ("all", "lid"):
    show_object(fa.module_lid(), id="lid", name="module lid")
if PART in ("all", "backer"):
    show_object(fa.module_backer(), id="backer", name="module backer")
if PART in ("all", "frame"):
    show_object(fa.electrode_frame(), id="frame", name="electrode frame")
if PART in ("all", "cover"):
    show_object(fa.electrode_cover(), id="cover", name="electrode cover")
if PART == "parts":
    for k, v in fa.placements().items():
        show_object(v, id=k, name=k)
if PART == "eparts":
    for k, v in fa.electrode_placements().items():
        show_object(v, id=k, name=k)
    show_object(fa.electrode_band(), id="svc_band", name="loop band")
