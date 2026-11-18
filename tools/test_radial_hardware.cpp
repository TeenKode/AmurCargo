#include "RobotHardware.h"
#include <cassert>
#include <cstdio>
void cmd(RobotHardware &h,const char *s){char b[160];strcpy(b,s);h.handle(b,clockMs);}
void steps(RobotHardware &h,int count){for(int i=0;i<count;i++){clockMs+=10;h.tick();}}
void sample(RobotHardware &h,const char *name,int adc){for(int i=14;i<=16;i++)adcPins[i]=adc;cmd(h,name);steps(h,32);assert(!h.calibrating);}
int main(){
 for(int i=0;i<32;i++)inputPins[i]=HIGH;
 RobotHardware h;h.init();assert(h.configError==0&&!h.armed&&!h.calibrationReady());
 h.releaseButton(2200,clockMs);h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);
 sample(h,"cal white",800);sample(h,"cal black",200);sample(h,"cal left",500);sample(h,"cal right",368);assert(h.calibrationReady());
 assert(normalizeAdc(800,800,200)==0&&normalizeAdc(200,800,200)==1000&&normalizeAdc(500,800,200)==500);
 cmd(h,"save");RobotHardware restored;restored.init();assert(restored.calibrationReady());
 cmd(h,"arm");cmd(h,"jog 100 -100 100");assert(h.jogging);steps(h,5);assert(outputPins[5]>0&&outputPins[6]>0);steps(h,6);assert(!h.jogging&&outputPins[5]==0&&outputPins[6]==0);
 cmd(h,"high");steps(h,250);assert(h.robot.servoAngle==h.v(P_LIFT_HIGH));h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);
 cmd(h,"low");steps(h,250);assert(h.robot.servoAngle==h.v(P_LIFT_LOW));h.releaseButton(100,clockMs);assert(h.robot.active());
 cmd(h,"jog 100 100 1000");assert(!h.jogging);const int angle=h.robot.servoAngle;cmd(h,"stop");steps(h,2);assert(h.robot.state==FAULT&&h.robot.fault==ABORTED&&outputPins[5]==0&&outputPins[6]==0&&h.robot.servoAngle==angle);
 cmd(h,"high");steps(h,250);cmd(h,"reset");assert(h.robot.state==FAULT);cmd(h,"low");steps(h,250);cmd(h,"reset");assert(h.robot.state==IDLE&&!h.armed);
 inputPins[h.v(P_CONTACT_PIN)]=LOW;cmd(h,"arm");h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);inputPins[h.v(P_CONTACT_PIN)]=HIGH;
 h.releaseButton(100,clockMs);assert(h.robot.active());inputPins[h.v(P_START_PIN)]=LOW;steps(h,5);assert(h.robot.state==FAULT&&h.robot.fault==ABORTED&&outputPins[5]==0&&outputPins[6]==0);inputPins[h.v(P_START_PIN)]=HIGH;
 EEPROM.bytes[15]^=1;RobotHardware bad;bad.init();assert(!bad.calibrationReady());
 h.settings.v[P_DRIVER_MODE]=1;h.settings.v[P_LEFT_IN1]=3;h.settings.v[P_LEFT_IN2]=5;h.settings.v[P_RIGHT_IN1]=6;h.settings.v[P_RIGHT_IN2]=11;h.outputMotors(90,-80);assert(outputPins[3]==90&&outputPins[5]==0&&outputPins[6]==0&&outputPins[11]==80);
 memset(EEPROM.bytes,0,sizeof(EEPROM.bytes));RobotHardware inv;inv.init();assert(!inv.servoReversed&&inv.lift.position==20);
 cmd(inv,"servo reverse");assert(!inv.servoReversed);
 cmd(inv,"servo reverse detached");assert(inv.servoReversed&&inv.lift.position==160&&!inv.armed);
 cmd(inv,"high");steps(inv,250);assert(inv.robot.servoAngle==140&&inv.lift.position==40);
 cmd(inv,"servo normal detached");assert(inv.servoReversed);
 cmd(inv,"low");steps(inv,250);assert(inv.lift.position==160);
 RobotHardware invBoot;invBoot.init();assert(invBoot.servoReversed&&invBoot.lift.position==160);
 cmd(invBoot,"erase");RobotHardware erased;erased.init();assert(erased.servoReversed&&!erased.calibrationReady());
 EEPROM.bytes[15]^=1;RobotHardware damagedCal;damagedCal.init();assert(damagedCal.servoReversed&&damagedCal.lift.position==160);
 cmd(damagedCal,"servo normal detached");assert(!damagedCal.servoReversed&&damagedCal.lift.position==20);
 cmd(damagedCal,"angle 31");
 cmd(damagedCal,"limits 31 119");assert(damagedCal.v(P_LIFT_LOW)==20);
 steps(damagedCal,30);assert(damagedCal.lift.position==31);
 cmd(damagedCal,"limits 119 31");assert(damagedCal.v(P_LIFT_LOW)==20);
 cmd(damagedCal,"limits 31 119");assert(damagedCal.v(P_LIFT_LOW)==31);
 RobotHardware calibrated;calibrated.init();assert(calibrated.lift.position==31);
 cmd(calibrated,"high");steps(calibrated,250);assert(calibrated.lift.position==119);
 assert(calibrated.v(P_LIFT_HIGH)==119);
 cmd(calibrated,"stream on");assert(calibrated.stream);
 cmd(calibrated,"stream off");assert(!calibrated.stream);
 puts("PASS: hardware adapter including independent persistent servo inversion, startup output, high/low mapping, detached confirmation, raised-fork lock and sensor-calibration erase/CRC independence");
}
