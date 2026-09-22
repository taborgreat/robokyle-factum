# Renders every part in rk_parts side by side so the solids can be eyeballed against the real hardware.
# agentcad run cad/parts_gallery.py --label parts
from rk_parts import PARTS, bbox_str
from build123d import Location

x = 0.0
for name, fn in PARTS.items():
    s = fn() if name != "pico_usb_plug" else fn()
    b = s.bounding_box()
    s = s.moved(Location((x - b.min.X, 0, -b.min.Z)))
    show_object(s, id=name, name=f"{name} {bbox_str(s)}")
    x += b.size.X + 8
