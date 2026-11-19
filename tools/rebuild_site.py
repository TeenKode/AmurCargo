"""Build offline simulation and embedded firmware from one canonical source directory."""
import json
import subprocess
import sys
from firmware_artifacts import ROOT, FIRMWARE_BUILD, verify_artifact

def current_artifacts():
    for binary,manifest,target in (
        ('Firmware_Uno.bin','Flash_Image.json','uno'),
        ('Firmware_Nano.bin','Flash_Image_Nano.json','nano'),
        ('FirmwareCore.wasm','FirmwareCore.json','wasm'),
    ):
        try:
            meta=json.loads((FIRMWARE_BUILD / manifest).read_text(encoding='utf-8'))
            data=(FIRMWARE_BUILD / binary).read_bytes()
            verify_artifact(data,meta,target,'python tools/rebuild_site.py')
        except (FileNotFoundError,ValueError,SystemExit):
            return False
    return True

def run(script):
    subprocess.run([sys.executable,str(ROOT/'tools'/script)],cwd=ROOT,check=True)

if not current_artifacts():
    print('Firmware changed: rebuilding UNO, Nano and WASM from firmware/RadialRobot.')
    for script in ('build_flash_image.py','build_nano_firmware.py','compile_radial_wasm.py'):
        run(script)
    if not current_artifacts():
        raise SystemExit('Generated firmware failed source and checksum verification')

for script in ('build_quick_guide.py','build_calibration_guide.py','build_radial_page.py','build_radial_3d.py','finalize_portable_page.py','build_illustrated_assembly.py','build_purchase_list.py','build_offline_all.py'):
    run(script)
print('Rebuilt self-contained 3D simulator and unified offline HTML from canonical sources')
