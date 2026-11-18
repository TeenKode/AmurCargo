from pathlib import Path
import subprocess,sys,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'simulator'
subprocess.run([sys.executable,str(R/'tools/compile_radial_avr.py'),'nano'],check=True)
memory=bytearray([255]*32768);end=0
for line in (O/'RadialRobot_NANO.hex').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  a=int.from_bytes(b[1:3],'big');memory[a:a+b[0]]=b[4:4+b[0]];end=max(end,a+b[0])
image=memory[:end];offset=image.find(b'AMURCFG2026V001!');assert offset>=0 and image.find(b'AMURCFG2026V001!',offset+1)<0;assert end<=30720
(O/'Firmware_Nano.bin').write_bytes(image)
meta=json.loads((O/'Flash_Image.json').read_text(encoding='utf-8'));meta.update(board='Arduino Nano / ATmega328P / 16 MHz',flash_limit=30720,configuration_offset=offset+16,crc_offset=offset+456,bytes=end,sha256=hashlib.sha256(image).hexdigest(),compatible_bootloaders=['ATmegaBOOT_168_atmega328 @ 57600','Optiboot @ 115200'],physical_upload_tested=False)
(O/'Flash_Image_Nano.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');print('Nano image',end,'bytes; byte-identical to UNO:',image==(O/'Firmware_Uno.bin').read_bytes())
