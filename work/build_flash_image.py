from pathlib import Path
import json,struct,subprocess,hashlib,base64
R=Path(__file__).resolve().parents[1];O=R/'outputs/AmurCargo_Radial';H=O/'RadialRobot/RobotConfig.h'
schema=json.loads((O/'settings_schema.json').read_text(encoding='utf-8'))
def crc(data):
 n=65535
 for b in data:
  n^=b<<8
  for _ in range(8):n=((n<<1)^0x1021 if n&0x8000 else n<<1)&65535
 return n
values=[p['default'] for p in schema['params']]+[p['default'] for h in range(2) for r in range(8) for p in schema['zones']]
payload=struct.pack('<216H8B',*values,1,2,3,4,5,6,7,7);assert len(payload)==440
blob=b'AMURCFG2026V001!'+payload+struct.pack('<H',crc(payload));assert len(blob)==458
normal=H.read_text(encoding='utf-8');normal=normal.split('// WEB_FLASH_CONFIG')[0]
normal=normal.replace('inline void loadUserSettings(Settings &s)', 'inline void loadDefaultSettings(Settings &s)')
addon='''
// WEB_FLASH_CONFIG: fixed-size flash configuration patched by the offline page.
#ifdef ARDUINO_ARCH_AVR
#include <avr/pgmspace.h>
static_assert(sizeof(Settings)==440,"Web flash configuration layout changed");
const uint8_t firmwareConfig[] PROGMEM __attribute__((used))={%s};
inline void loadUserSettings(Settings &s){
 memcpy_P(&s,firmwareConfig+16,sizeof(s));uint16_t crc=65535;const uint8_t *p=(const uint8_t*)&s;
 for(uint16_t i=0;i<sizeof(s);i++){crc^=(uint16_t)p[i]<<8;for(uint8_t j=0;j<8;j++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}
 if(crc!=pgm_read_word(firmwareConfig+16+sizeof(s)))s.v[0]=65535;
}
#else
inline void loadUserSettings(Settings &s){loadDefaultSettings(s);}
#endif
'''%','.join(map(str,blob))
H.write_text(normal+addon,encoding='utf-8')
subprocess.run([__import__('sys').executable,str(R/'work/compile_radial_avr.py')],check=True)
memory=bytearray([255]*32768);end=0
for line in (O/'RadialRobot_UNO.hex').read_text().splitlines():
 b=bytes.fromhex(line[1:]);assert sum(b)%256==0
 if b[3]==0:
  a=int.from_bytes(b[1:3],'big');memory[a:a+b[0]]=b[4:4+b[0]];end=max(end,a+b[0])
image=memory[:end];offset=image.find(blob);assert offset>=0 and image.find(blob,offset+1)==-1;assert end<=32256
(O/'Firmware_Uno.bin').write_bytes(image)
(O/'Flash_Image.json').write_text(json.dumps(dict(board='Arduino UNO / ATmega328P / Optiboot',baud=115200,page_size=128,flash_limit=32256,configuration_offset=offset+16,configuration_size=440,crc_offset=offset+456,bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),signature=[30,149,15],physical_upload_tested=False),indent=2),encoding='utf-8');print('Patchable firmware',end,'bytes; settings offset',offset+16)
