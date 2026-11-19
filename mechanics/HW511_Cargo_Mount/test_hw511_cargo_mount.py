"""Local geometric QA for the experimental HW-511 cargo mount.

Requires openscad CLI and trimesh (see project requirements.txt).
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import trimesh

HERE = Path(__file__).resolve().parent
MODEL = HERE / "hw511_cargo_mount.scad"
assert MODEL.is_file(), MODEL
assert shutil.which("openscad"), "Install OpenSCAD to run geometric checks"
with TemporaryDirectory() as directory:
    stl = Path(directory) / "mount.stl"
    subprocess.run(
        ["openscad", "-o", str(stl), "-D", 'view="part"', str(MODEL)],
        check=True, capture_output=True,
    )
    mesh = trimesh.load(stl, force="mesh")
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
    assert len(mesh.split()) == 1
    assert all(abs(a-b) < 0.01 for a, b in zip(mesh.extents, [15.0, 18.8, 51.5])), mesh.extents
    # The inner surfaces of the two fork rails start at X +/-9.5 mm.
    assert mesh.bounds[0, 0] > -9.5 and mesh.bounds[1, 0] < 9.5
    # A 1 mm adhesive gap above the existing spine's front Y=4 surface.
    assert abs(mesh.bounds[0, 1] - 5) < 0.01
    print("PASS: watertight single printable part, dimensions, fork-lane clearance")
