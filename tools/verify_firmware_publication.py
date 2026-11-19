"""Check that the published offline HTML uses the exact firmware built from source.

Run after tools/rebuild_site.py, and again after downloading the build artifact.
The check requires only Python's standard library; no toolchains or network calls.
"""
import base64
import json
from pathlib import Path

from firmware_artifacts import FIRMWARE_BUILD, ROOT, verify_artifact

SITE = ROOT / "simulator/Open_Simulation_3D.html"


def verify():
    for filename, manifest, target in (
        ("Firmware_Uno.bin", "Flash_Image.json", "uno"),
        ("Firmware_Nano.bin", "Flash_Image_Nano.json", "nano"),
        ("FirmwareCore.wasm", "FirmwareCore.json", "wasm"),
    ):
        image = (FIRMWARE_BUILD / filename).read_bytes()
        metadata = json.loads((FIRMWARE_BUILD / manifest).read_text(encoding="utf-8"))
        verify_artifact(image, metadata, target, "python tools/rebuild_site.py")
        if target != "wasm" and metadata["bytes"] != len(image):
            raise AssertionError(f"{filename}: size in manifest does not match binary")

    if (FIRMWARE_BUILD / "Firmware_Uno.bin").read_bytes() != (
        FIRMWARE_BUILD / "Firmware_Nano.bin"
    ).read_bytes():
        raise AssertionError("UNO and Nano binaries must match until separate images are embedded")

    html = SITE.read_text(encoding="utf-8")
    if "window.AMUR_PROJECT_SOURCES=" not in html:
        raise AssertionError("Arduino source bundle is not embedded in the HTML")
    for filename in ("FirmwareCore.wasm", "Firmware_Uno.bin"):
        encoded = base64.b64encode((FIRMWARE_BUILD / filename).read_bytes()).decode("ascii")
        if html.count(encoded) != 1:
            raise AssertionError(f"HTML must contain exactly one current {filename}")

    for board in ("UNO", "NANO"):
        if not (FIRMWARE_BUILD / f"RadialRobot_{board}.hex").is_file():
            raise AssertionError(f"Missing Arduino HEX for {board}")
    print("PASS: firmware source digests, embedded WASM/UNO, Nano parity and HEX images")


if __name__ == "__main__":
    verify()
