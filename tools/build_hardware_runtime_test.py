from pathlib import Path
import subprocess,tarfile,sys,re,json,os
R=Path(__file__).resolve().parents[1];D=R/'tools/avr_hardware_test';D.mkdir(exist_ok=True)
shim='''#pragma once
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
typedef uint8_t byte;
const uint8_t A0=14,A1=15,A2=16,A3=17,A4=18,A5=19;
const int LOW=0,HIGH=1,OUTPUT=1,INPUT_PULLUP=2;
#define F(x) x
static uint32_t clockMs=0;
static int inputPins[32],outputPins[32],adcPins[32];
inline uint32_t millis(){return clockMs;}
inline void pinMode(uint8_t,int){}
inline int digitalRead(uint8_t p){return inputPins[p];}
inline void digitalWrite(uint8_t p,int v){outputPins[p]=v;}
inline void analogWrite(uint8_t p,int v){outputPins[p]=v;}
inline int analogRead(uint8_t p){return adcPins[p];}
struct SerialMock {void begin(long){} int available(){return 0;} char read(){return 0;} template<class T>void print(T){} template<class T>void println(T){} void println(){} };
static SerialMock Serial;
'''
(D/'Arduino.h').write_text(shim,encoding='utf-8')
(D/'Servo.h').write_text('#pragma once\nclass Servo{public:int position=0;void write(int a){position=a;}void attach(int){}};\n')
(D/'EEPROM.h').write_text('#pragma once\n#include <string.h>\nstruct EEPROMMock{unsigned char bytes[1024];template<class T>void get(int a,T &v){memcpy(&v,bytes+a,sizeof(v));}template<class T>void put(int a,const T &v){memcpy(bytes+a,&v,sizeof(v));}};static EEPROMMock EEPROM;\n')
test=(R/'tools/test_radial_hardware.cpp').read_text(encoding='utf-8').replace('#include <cassert>','').replace('#include <cstdio>','#include <stdio.h>').replace('int main(){','void runTest(){')
prefix='volatile uint16_t testStatus=0;\n#define assert(x) do{if(!(x)){testStatus=__LINE__;for(;;){}}}while(0)\n'
(D/'test.cpp').write_text('#include <stdint.h>\n'+prefix+test+'\nint main(){testStatus=1;runTest();testStatus=65535;for(;;){}}\n',encoding='utf-8')
SDK=Path(os.environ.get('ARDUINO_DATA',str(Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'Arduino15')))
TC=sorted((SDK/'packages/arduino/tools/avr-gcc').iterdir())[-1]/'bin';src=R/'firmware/RadialRobot'
subprocess.run([str(TC/'avr-g++.exe'),'-mmcu=atmega1284p','-Os','-std=gnu++1z','-fno-exceptions','-fno-rtti','-I'+str(D),'-I'+str(src),str(D/'test.cpp'),'-o',str(D/'test.elf')],check=True)
subprocess.run([str(TC/'avr-objcopy.exe'),'-O','binary',str(D/'test.elf'),str(D/'test.bin')],check=True)
symbols=subprocess.check_output([str(TC/'avr-nm.exe'),str(D/'test.elf')]).decode();address=int(re.search(r'^([0-9a-f]+) [A-Za-z] testStatus\r?$',symbols,re.M).group(1),16)-0x800000
(D/'meta.json').write_text(json.dumps(dict(status_address=address)),encoding='utf-8')
if (R/'tools/avr8js-0.21.1.tgz').exists():
 with tarfile.open(R/'tools/avr8js-0.21.1.tgz') as tf:tf.extractall(D/'avr8js',filter='data')
print('Compiled actual hardware adapter tests for AVR CPU; status address',address)
