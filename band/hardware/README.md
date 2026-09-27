# Band hardware

`cad/` is the build123d/agentcad source, `print/` the exported STLs (with sizes in `MANIFEST.md`), `../BENCH.md` the
electronics build guide. Pins: [../PINOUT.md](../PINOUT.md). Box, lid and plate print in PLA Tough (the clearances in `DIM` were measured on prints in it); PETG is
reserved for the claw.

## Setup (done once, Windows)
```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe "agentcad[mcp]" build123d trimesh numpy
echo <repo>\band\hardware\cad > .venv\Lib\site-packages\robokyle_cad.pth   # makes rk_parts importable (absolute path)
```
`agentcad.toml` sends generated versions to `build/` (git-ignored). `.mcp.json` exposes agentcad to Claude Code.
Set `PYTHONUTF8=1` in the shell: agentcad's JSON writer trips on the Windows console codepage otherwise.

## Files
- `rk_parts.py` — every real part as a named solid + keep-out. `DIM` holds all numbers with a source flag
  (D datasheet / M measured / G guess). Pockets are cut from keep-outs + `clr`, never from bare parts.
- `parts_gallery.py` — renders every part in a row; run it after changing `DIM` to eyeball against the hardware.
- `band_box.py` / `band_plate.py` — the cuff box, lid and sewn plate (`*_run.py` are the agentcad entry points).
- `forearm.py` — the forearm module, its lid and backer, the electrode frames and covers (`python forearm.py` runs its checks).
- `arm_model.py` — stand-in forearm for the viewer's whole-arm view.
- `check_box.py` — intersects every part with the box, lid and envelope; run after every change.
- `publish.py` — copies a version's STL into `print/`, records the mesh bounding box in `print/MANIFEST.md` and
  rebuilds the viewer (`band/software/viewer/build_viewer.py`).

## Workflow
```
.venv\Scripts\agentcad run band\hardware\cad\band_box_run.py --label band_box --params PART=box --export stl --no-view --no-diff
.venv\Scripts\python band\hardware\cad\publish.py band_box band_box
.venv\Scripts\python band\hardware\cad\check_box.py      # interference check: must PASS before any export
```
Read `build/vN_label/preview.png` after every run. `--dry-run` for metrics only. Export STL only when `is_valid` is true.

