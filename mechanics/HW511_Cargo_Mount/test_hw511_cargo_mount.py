"""HW-511 mount geometry checks. Requires OpenSCAD CLI and trimesh."""
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import shutil
import subprocess

import trimesh

HERE = Path(__file__).resolve().parent
SCAD = HERE / "hw511_cargo_mount.scad"
code = SCAD.read_text(encoding="utf-8")
assert "pcb_length = 42.0;" in code
assert "pcb_width = 10.5;" in code
assert "hole_from_nose = [4.0, 15.0];" in code
assert "bolt_clearance = 2.9;" in code
assert shutil.which("openscad"), "Install OpenSCAD to run geometric checks"
with TemporaryDirectory() as temp:
    for view in ("part", "board"):
        dest = Path(temp) / f"hw511_{view}.stl"
        subprocess.run(
            ["openscad", "-o", str(dest), "-D", f'view="{view}"', str(SCAD)],
            check=True, capture_output=True, text=True,
        )
        mesh = trimesh.load(dest, force="mesh")
        assert mesh.is_watertight, f"{view}: mesh is not watertight"
        assert mesh.is_winding_consistent, f"{view}: invalid normals"
        assert mesh.volume > 0, f"{view}: invalid volume"
        if view == "part":
            assert len(mesh.split()) == 1, "Mount must print as one object"
            assert max(abs(float(a-b)) for a,b in zip(mesh.extents, [15.0, 19.2, 45.0])) < .01, mesh.extents
            assert mesh.bounds[0][0] > -9.5 and mesh.bounds[1][0] < 9.5, "Fork clearance"
            assert abs(mesh.bounds[0][1] - 5.0) < .01, "Spine tape gap"
        else:
            # PCB and components are many separate bodies by design.
            assert mesh.bounds[1][2] > 60.0, "Header pins absent"
    print("PASS: mount is one watertight solid, 15 x 19.2 x 45 mm; board envelope and 42 x 10.5 outline defined")