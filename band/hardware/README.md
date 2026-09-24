# Band hardware

`cad/` is the build123d/agentcad source, `print/` the exported STLs (with sizes in `MANIFEST.md`), `../BENCH.md` the
electronics build guide. Pins: [../PINOUT.md](../PINOUT.md). Box, lid and plate print in PLA Tough (the same
filament the fit gauge was printed with - clearances were measured on it); PETG is reserved for the claw.

## Setup (done once, Windows)
```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe "agentcad[mcp]" build123d trimesh numpy
echo C:\Users\Tabor\Documents\GitHub\robokyle-factum\band\hardware\cad > .venv\Lib\site-packages\robokyle_cad.pth   # makes rk_parts importable
```
`agentcad.toml` sends generated versions to `build/` (git-ignored). `.mcp.json` exposes agentcad to Claude Code.
Set `PYTHONUTF8=1` in the shell: agentcad's JSON writer trips on the Windows console codepage otherwise.

## Files
- `rk_parts.py` — every real part as a named solid + keep-out. `DIM` holds all numbers with a source flag
  (D datasheet / M measured / G guess). Pockets are cut from keep-outs + `clr`, never from bare parts.
- `parts_gallery.py` — renders every part in a row; run it after changing `DIM` to eyeball against the hardware.
- `fit_gauge.py` — printed go/no-go gauge: stepped slots per part, hole and slot ladders. Gives the printer's
  real clearances without calipers. Print it first.
- `band_box.py` / `band_plate.py` — the cuff box, lid and sewn plate (`*_run.py` are the agentcad entry points).
- `check_box.py` — intersects every part with the box, lid and envelope; run after every change.
- `publish.py` — copies a version's STL into `print/` and records the mesh bounding box in `print/MANIFEST.md`.

## Workflow
```
.venv\Scripts\agentcad run band\hardware\cad\band_box_run.py --label band_box --params PART=box --export stl --no-view --no-diff
.venv\Scripts\python band\hardware\cad\publish.py band_box band_box
.venv\Scripts\python band\hardware\cad\check_box.py      # interference check: must PASS before any export
```
Read `build/vN_label/preview.png` after every run. `--dry-run` for metrics only. Export STL only when `is_valid` is true.

## Reading the fit gauge
- Stepped slots (labels BATT, STRIP, PICO on the top edge; IMU, CHG, SW, EMG on the bottom): push the part in
  edge-first, square to the plate. Steps from the mouth inward are +1.2 / +0.8 / +0.5 / +0.2 mm total width.
  Report the deepest step the part reaches without force (1-4). 4 = snug press fit, 1 = loose.
- Hole ladders: LED 3.0/3.2/3.4/3.6, MOT (coin motor) 10.2/10.5/10.8, BTN (6 mm tactile body) 6.6/7.0/7.4,
  M2 thread-forming 1.6/1.8/2.0/2.2, INS heat-set insert 3.0/3.2/3.4. Report the first hole each part enters
  (for M2: the smallest hole a screw will bite into by hand; for INS: the hole the insert sits in before heating).
- Rect slots: NUB = switch actuator+travel 6x3 / 7x3.4 / 8x3.8; PH2/PH3 = JST-PH 2- and 3-pin housings.
- The chamfered corner marks the origin; labels face up.
