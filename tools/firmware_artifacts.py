"""Fingerprint the inputs and bytes of each firmware artifact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / 'simulator'
SKETCH = ROOT / 'firmware/RadialRobot'
FIRMWARE_BUILD = ROOT / 'firmware/build'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_digest(target):
    if target == 'wasm':
        paths = [SKETCH / 'WebAssembly.cpp', SKETCH / 'RadialCore.h', SKETCH / 'Settings.h',
                 SKETCH / 'RobotConfig.h']
    else:
        paths = sorted(p for p in SKETCH.iterdir() if p.suffix in {'.h', '.ino'})
    records = {p.relative_to(ROOT).as_posix(): sha256(p.read_text(encoding='utf-8').encode())
               for p in paths}
    return sha256(json.dumps(records, sort_keys=True).encode())


def verify_artifact(data, metadata, target, rebuild):
    if (metadata.get('source_sha256') != source_digest(target)
            or metadata.get('sha256') != sha256(data)):
        raise SystemExit(f'{target} artifact does not match its sources or checksum. Run {rebuild}.')
