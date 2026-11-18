from pathlib import Path
import sys,subprocess,re,base64,hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'simulator'
if not (O/'Firmware_Uno.bin').exists():
 page=(O/'Open_Simulation_3D.html').read_text(encoding='utf-8');found=re.search(r"base:Uint8Array\.from\(atob\('([^']+)'",page)
 if not found:raise SystemExit('Compile the firmware first: python tools/build_flash_image.py')
 (O/'Firmware_Uno.bin').write_bytes(base64.b64decode(found.group(1)))
nano = O / 'Firmware_Nano.bin'
if not nano.exists():
 image = (O / 'Firmware_Uno.bin').read_bytes()
 metadata = json.loads((O / 'Flash_Image_Nano.json').read_text(encoding='utf-8'))
 if hashlib.sha256(image).hexdigest() == metadata['sha256']:
  nano.write_bytes(image)
tasks=['build_radial_page.py','build_radial_3d.py','finalize_portable_page.py']
for task in tasks:subprocess.run([sys.executable,str(R/'tools'/task)],cwd=R,check=True)
print('Rebuilt self-contained 3D simulator')
