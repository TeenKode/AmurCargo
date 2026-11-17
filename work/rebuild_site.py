from pathlib import Path
import sys,subprocess,re,base64
R=Path(__file__).resolve().parents[1];O=R/'outputs/AmurCargo_Radial'
if not (O/'Firmware_Uno.bin').exists():
 page=(O/'Open_Simulation_3D.html').read_text(encoding='utf-8');found=re.search(r"base:Uint8Array\.from\(atob\('([^']+)'",page)
 if not found:raise SystemExit('Compile the firmware first: python work/build_flash_image.py')
 (O/'Firmware_Uno.bin').write_bytes(base64.b64decode(found.group(1)))
tasks=['build_radial_page.py','build_radial_3d.py','finalize_portable_page.py']
for task in tasks:subprocess.run([sys.executable,str(R/'work'/task)],cwd=R,check=True)
print('Rebuilt self-contained 3D simulator')
