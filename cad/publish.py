"""Copy an agentcad version's STL into print/<name>.stl and record its mesh bounding box in print/MANIFEST.md.

    .venv/Scripts/python.exe cad/publish.py <version_dir_or_label> <name>
    e.g.  python cad/publish.py gauge fit_gauge

Overwrites in place so print/ never holds stale copies. The manifest line is what to check against
Bambu Studio's size readout after loading the file.
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
BUILD, PRINT = ROOT / "build", ROOT / "print"


def find_version(ref: str) -> Path:
    p = Path(ref)
    if p.is_dir():
        return p
    cands = sorted(BUILD.glob(f"v*_{ref}"), key=lambda d: int(re.match(r"v(\d+)_", d.name).group(1)))
    if not cands:
        sys.exit(f"no version dir for '{ref}' under {BUILD}")
    return cands[-1]


def main(ref: str, name: str):
    vdir = find_version(ref)
    src = vdir / "output.stl"
    if not src.exists():
        sys.exit(f"{src} missing: rerun with --export stl")
    PRINT.mkdir(exist_ok=True)
    dst = PRINT / f"{name}.stl"
    shutil.copyfile(src, dst)
    m = trimesh.load(dst)
    ext = m.bounding_box.extents
    line = (f"| {name}.stl | {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} | {m.volume/1000:.1f} cm3 | "
            f"{'yes' if m.is_watertight else 'NO'} | {vdir.name} | {date.today()} |")
    man = PRINT / "MANIFEST.md"
    header = ("| file | size mm (X x Y x Z) | volume | watertight | source version | date |\n"
              "|---|---|---|---|---|---|\n")
    rows = {}
    if man.exists():
        for l in man.read_text().splitlines():
            if l.startswith("| ") and not l.startswith("| file") :
                rows[l.split("|")[1].strip()] = l
    rows[f"{name}.stl"] = line
    man.write_text("# Print outputs (overwritten in place; check sizes in Bambu Studio)\n\n" + header
                   + "\n".join(rows[k] for k in sorted(rows)) + "\n")
    print(line)


if __name__ == "__main__":
    main(*sys.argv[1:3])
