from pathlib import Path
import subprocess,json,hashlib,sys,os
board=sys.argv[1] if len(sys.argv)>1 else 'uno'
assert board in ('uno','nano')
R=Path(__file__).resolve().parents[1];OUT=R/'outputs/AmurCargo_Radial';SK=OUT/'RadialRobot';BUILD=R/'work/radial_avr_build';BUILD.mkdir(exist_ok=True)
SDK=Path(os.environ.get('ARDUINO_DATA',str(Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'Arduino15')));TC=sorted((SDK/'packages/arduino/tools/avr-gcc').iterdir())[-1];CORE=sorted((SDK/'packages/arduino/hardware/avr').iterdir())[-1];SERVO=SDK/'libraries/Servo'
if not SERVO.exists():SERVO=Path(os.environ.get('ARDUINO_SERVO',str(Path.home()/'Documents/Arduino/libraries/Servo')))
includes=[CORE/'cores/arduino',CORE/('variants/eightanaloginputs' if board=='nano' else 'variants/standard'),CORE/'libraries/EEPROM/src',SERVO/'src',SK]
common=['-c','-Os','-ffunction-sections','-fdata-sections','-flto','-mmcu=atmega328p','-DF_CPU=16000000L','-DARDUINO=10819','-DARDUINO_AVR_'+board.upper(),'-DARDUINO_ARCH_AVR']+['-I'+str(x) for x in includes]
sources=list((CORE/'cores/arduino').glob('*.cpp'))+list((CORE/'cores/arduino').glob('*.c'))+list((CORE/'cores/arduino').glob('*.S'))+[SERVO/'src/avr/Servo.cpp',SK/'RadialRobot.ino'];objects=[]
for index,source in enumerate(sources):
 cpp=source.suffix in ('.cpp','.ino');compiler=TC/'bin'/('avr-g++.exe' if cpp else 'avr-gcc.exe');obj=BUILD/(str(index)+'_'+source.name+'.o');objects.append(obj)
 args=[str(compiler),*common]+(['-std=gnu++11','-fno-exceptions','-fno-threadsafe-statics','-fpermissive'] if cpp else ['-std=gnu11'])
 if source.suffix=='.ino':args+=['-x','c++']
 if source.suffix=='.S':args+=['-x','assembler-with-cpp']
 result=subprocess.run(args+[str(source),'-o',str(obj)],capture_output=True)
 if result.returncode:print(result.stderr.decode(errors='replace'));raise SystemExit(result.returncode)
elf=OUT/('RadialRobot_'+board.upper()+'.elf');hexfile=OUT/('RadialRobot_'+board.upper()+'.hex')
args=[str(TC/'bin/avr-gcc.exe'),'-Os','-flto','-fuse-linker-plugin','-mmcu=atmega328p','-Wl,--gc-sections','-o',str(elf)]+[str(x) for x in objects]+['-lm']
r=subprocess.run(args,capture_output=True)
if r.returncode:print(r.stderr.decode(errors='replace'));raise SystemExit(r.returncode)
subprocess.run([str(TC/'bin/avr-objcopy.exe'),'-O','ihex','-R','.eeprom',str(elf),str(hexfile)],check=True)
size=subprocess.check_output([str(TC/'bin/avr-size.exe'),str(elf)]).decode(errors='replace');print(size)
parts=size.splitlines()[1].split();text,data,bss=map(int,parts[:3]);assert text+data<=32256;assert data+bss<1600
report=dict(board='Arduino UNO R3 / ATmega328P, 16 MHz',compiler=TC.name,arduino_core=CORE.name,servo_library=(SERVO/'library.properties').read_text(encoding='utf-8').split('version=')[1].splitlines()[0],flash_bytes=text+data,flash_limit=32256,static_ram_bytes=data+bss,ram_limit=2048,hex_sha256=hashlib.sha256(hexfile.read_bytes()).hexdigest(),compile_and_link=True,flashed_to_hardware=False)
if board=='nano':report.update(board='Arduino Nano / ATmega328P, 16 MHz',flash_limit=30720,variant='eightanaloginputs');assert text+data<=30720
(OUT/('Nano_Build_Checks.json' if board=='nano' else 'AVR_Build_Checks.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
