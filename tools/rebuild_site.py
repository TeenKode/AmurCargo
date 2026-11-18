import base64
import json
import re
import subprocess
import sys

from firmware_artifacts import ROOT, SIMULATOR, verify_artifact

images = {}
for board, suffix in [('Uno', ''), ('Nano', '_Nano')]:
    metadata = json.loads((SIMULATOR / f'Flash_Image{suffix}.json').read_text(encoding='utf-8'))
    binary = SIMULATOR / f'Firmware_{board}.bin'
    if binary.is_file():
        data = binary.read_bytes()
    else:
        page = (SIMULATOR / 'Open_Simulation_3D.html').read_text(encoding='utf-8')
        found = re.search(r"base:Uint8Array\.from\(atob\('([^']+)'", page)
        data = base64.b64decode(found[1]) if found else b''
    command = 'python tools/build_flash_image.py'
    if board == 'Nano':
        command += ' followed by python tools/build_nano_firmware.py'
    verify_artifact(data, metadata, board, command)
    images[binary] = data

wasm = (SIMULATOR / 'FirmwareCore.wasm').read_bytes()
metadata = json.loads((SIMULATOR / 'FirmwareCore.json').read_text(encoding='utf-8'))
verify_artifact(wasm, metadata, 'wasm', 'python tools/compile_radial_wasm.py')

for binary, data in images.items():
    binary.write_bytes(data)
for script in ('build_radial_page.py', 'build_radial_3d.py', 'finalize_portable_page.py'):
    subprocess.run([sys.executable, str(ROOT / 'tools' / script)], cwd=ROOT, check=True)
print('Rebuilt self-contained 3D simulator')
