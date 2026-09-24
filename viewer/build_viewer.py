"""Rebuild viewer/glb.js from the CURRENT prints.

    .venv/Scripts/python viewer/build_viewer.py            # embed the GLBs behind print/*.stl (per MANIFEST.md) + latest parts/arm
    .venv/Scripts/python viewer/build_viewer.py --parts    # first re-export the placed-parts and arm GLBs with agentcad

publish.py calls this after every publish, so viewer/index.html always shows what is in print/. Open the HTML
straight from disk; the models are embedded in glb.js (no server needed). The claude.ai copy is republished by hand.
"""
import base64, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD, PRINT, OUT = ROOT / "build", ROOT / "band" / "hardware" / "print", Path(__file__).with_name("glb.js")
PY = ROOT / ".venv" / "Scripts" / "python.exe"
CAD = "band/hardware/cad"

# viewer file -> the print it mirrors (version from MANIFEST.md)
PRINTS = {"band_box.glb": "band_box.stl", "band_lid.glb": "band_lid.stl", "band_plate.glb": "band_plate.stl",
          "fa_module.glb": "fa_module.stl", "fa_lid.glb": "fa_lid.stl", "fa_backer.glb": "fa_backer.stl",
          "electrode_frame.glb": "electrode_frame.stl", "electrode_bar.glb": "electrode_bar.stl"}
# viewer file -> (agentcad label, run script, PART) for the placed parts and the arm (latest version wins)
PARTS = {"band_parts.glb": ("band_parts", f"{CAD}/band_box_run.py", "parts"),
         "fa_parts.glb": ("fa_parts", f"{CAD}/forearm_run.py", "parts"),
         "electrode_parts.glb": ("fa_eparts", f"{CAD}/forearm_run.py", "eparts"),
         "arm.glb": ("arm", f"{CAD}/arm_model_run.py", None)}


def manifest_versions():
    v = {}
    for line in (PRINT / "MANIFEST.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\S+\.stl) \|.*\| (v\d+_\S+) \|", line)
        if m:
            v[m.group(1)] = m.group(2)
    return v


def latest(label):
    c = sorted(BUILD.glob(f"v*_{label}"), key=lambda d: int(re.match(r"v(\d+)_", d.name).group(1)))
    return c[-1] if c else None


def export_parts():
    for glb, (label, script, part) in PARTS.items():
        cmd = [str(ROOT / ".venv" / "Scripts" / "agentcad.exe"), "run", script, "--label", label, "--no-view", "--no-diff"]
        if part:
            cmd += ["--params", f"PART={part}"]
        print("agentcad", label, "...", end=" ", flush=True)
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
        print("ok" if '"status": "success"' in r.stdout else "FAILED\n" + r.stdout[-800:])


def main():
    if "--parts" in sys.argv:
        export_parts()
    vers = manifest_versions()
    data, versions, missing = {}, {}, []
    for glb, stl in PRINTS.items():
        vdir = BUILD / vers[stl] if stl in vers else None
        if not vdir or not (vdir / "output.glb").exists():
            missing.append(glb); continue
        data[glb] = base64.b64encode((vdir / "output.glb").read_bytes()).decode()
        versions[glb] = int(re.match(r"v(\d+)_", vdir.name).group(1))
    for glb, (label, _, _) in PARTS.items():
        vdir = latest(label)
        if not vdir or not (vdir / "output.glb").exists():
            missing.append(glb); continue
        data[glb] = base64.b64encode((vdir / "output.glb").read_bytes()).decode()
        versions[glb] = int(re.match(r"v(\d+)_", vdir.name).group(1))
    OUT.write_text("window.GLB=" + json.dumps(data) + ";\nwindow.GLB_VERSIONS=" + json.dumps(versions) + ";\n", encoding="utf-8")
    print(f"viewer/glb.js: {OUT.stat().st_size // 1024} kB, " + ", ".join(f"{k} v{v}" for k, v in versions.items()))
    if missing:
        print("MISSING (run with --parts or publish first):", ", ".join(missing))


if __name__ == "__main__":
    main()
