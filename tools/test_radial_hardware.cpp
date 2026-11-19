#include "RobotHardware.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
void cmd(RobotHardware &h,const char *s){char b[160];strcpy(b,s);h.handle(b,clockMs);}
void steps(RobotHardware &h,int count){for(int i=0;i<count;i++){clockMs+=10;h.tick();}}
void sample(RobotHardware &h,const char *name,int adc){for(int i=14;i<=16;i++)adcPins[i]=adc;cmd(h,name);steps(h,32);assert(!h.calibrating);}
int main(){
 for(int i=0;i<32;i++)inputPins[i]=HIGH;
 RobotHardware h;h.init();assert(h.configError==0&&!h.armed&&!h.calibrationReady());
 h.releaseButton(2200,clockMs);h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);
 sample(h,"cal white",800);sample(h,"cal black",200);sample(h,"cal left",500);sample(h,"cal right",368);assert(h.calibrationReady());
 assert(normalizeAdc(800,800,200)==0&&normalizeAdc(200,800,200)==1000&&normalizeAdc(500,800,200)==500);
 sample(h,"cal right",500);
 assert(h.calibrationState()==RobotHardware::CAL_HUB_OVERLAP);
 cmd(h,"arm");h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);
 cmd(h,"save");RobotHardware unsaved;unsaved.init();assert(!unsaved.calibrationReady());
 sample(h,"cal right",398); // 670 versus 500, with an inclusive tolerance of 85.
 assert(h.calibrationState()==RobotHardware::CAL_HUB_OVERLAP);
 h.settings.v[P_HUB_MODE]=1;assert(h.calibrationReady());h.settings.v[P_HUB_MODE]=0;
 sample(h,"cal right",397);assert(h.calibrationReady());
 sample(h,"cal right",368);assert(h.calibrationReady());
 cmd(h,"save");RobotHardware restored;restored.init();assert(restored.calibrationReady());
 cmd(h,"arm");cmd(h,"jog 100 -100 100");assert(h.jogging);steps(h,5);assert(outputPins[10]>0&&outputPins[11]>0);steps(h,6);assert(!h.jogging&&outputPins[10]==0&&outputPins[11]==0);
 for(int duration : {1000, 20}){
  cmd(h,"arm");
  cmd(h,duration==20?"jog 100 100 20":"jog 100 100 1000");
  assert(h.jogging);
  steps(h,1);
  inputPins[h.v(P_START_PIN)]=LOW;steps(h,5);
  assert(!h.jogging&&!h.armed&&outputPins[10]==0&&outputPins[11]==0);
  inputPins[h.v(P_START_PIN)]=HIGH;steps(h,5);
  assert(h.robot.state==IDLE&&!h.armed);
 }
 cmd(h,"arm");
 cmd(h,"high");steps(h,250);assert(h.robot.servoAngle==h.v(P_LIFT_HIGH));h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);
 cmd(h,"low");steps(h,250);assert(h.robot.servoAngle==h.v(P_LIFT_LOW));h.releaseButton(100,clockMs);assert(h.robot.active());
 cmd(h,"jog 100 100 1000");assert(!h.jogging);const int angle=h.robot.servoAngle;cmd(h,"stop");steps(h,2);assert(h.robot.state==FAULT&&h.robot.fault==ABORTED&&outputPins[10]==0&&outputPins[11]==0&&h.robot.servoAngle==angle);
 cmd(h,"high");steps(h,250);cmd(h,"reset");assert(h.robot.state==FAULT);cmd(h,"low");steps(h,250);cmd(h,"reset");assert(h.robot.state==IDLE&&!h.armed);
 inputPins[h.v(P_CONTACT_PIN)]=LOW;cmd(h,"arm");h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);inputPins[h.v(P_CONTACT_PIN)]=HIGH;
 h.releaseButton(100,clockMs);assert(h.robot.active());inputPins[h.v(P_START_PIN)]=LOW;steps(h,5);assert(h.robot.state==FAULT&&h.robot.fault==ABORTED&&outputPins[10]==0&&outputPins[11]==0);inputPins[h.v(P_START_PIN)]=HIGH;
 EEPROM.bytes[15]^=1;RobotHardware bad;bad.init();assert(!bad.calibrationReady());
 assert(h.v(P_DRIVER_MODE)==2&&h.v(P_CONTACT_PIN)==2&&h.v(P_LED_PIN)==255);
 h.outputMotors(90,-80);
 assert(outputPins[12]==HIGH&&outputPins[10]==90&&outputPins[13]==LOW&&outputPins[11]==80);
 h.outputMotors(0,0);assert(outputPins[10]==0&&outputPins[11]==0);
 Settings wrong=h.settings;wrong.v[P_SERVO_PIN]=10;assert(pinSettingsError(wrong)==305);
 wrong=h.settings;wrong.v[P_CONTACT_PIN]=12;assert(pinSettingsError(wrong)!=0);
 wrong=h.settings;wrong.v[P_START_PIN]=4;assert(pinSettingsError(wrong)==306);
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
 // Preview an angle: saving limits before it arrives is rejected.
 cmd(damagedCal,"angle 31");assert(damagedCal.manualServoPending);
 cmd(damagedCal,"limits 31 119");assert(damagedCal.v(P_LIFT_LOW)==20);
 steps(damagedCal,30);
 assert(damagedCal.lift.position==31&&damagedCal.manualServoPending);
 assert(!damagedCal.servoSettled(clockMs));
 cmd(damagedCal,"limits 31 119");assert(damagedCal.v(P_LIFT_LOW)==20);
 steps(damagedCal,45);
 assert(damagedCal.lift.position==31&&!damagedCal.manualServoPending&&damagedCal.servoSettled(clockMs));
 // Small step adjustments also produce one arrival confirmation.
 cmd(damagedCal,"angle 33");assert(damagedCal.manualServoPending);
 steps(damagedCal,10);assert(damagedCal.robot.servoAngle==33&&damagedCal.manualServoPending);
 steps(damagedCal,45);assert(!damagedCal.manualServoPending);
 cmd(damagedCal,"angle 31");steps(damagedCal,55);
 assert(damagedCal.robot.servoAngle==31&&!damagedCal.manualServoPending);
 cmd(damagedCal,"angle 180");steps(damagedCal,350);
 assert(damagedCal.robot.servoAngle==180&&damagedCal.lift.position==180&&!damagedCal.manualServoPending);
 cmd(damagedCal,"angle 0");steps(damagedCal,450);
 assert(damagedCal.robot.servoAngle==0&&damagedCal.lift.position==0&&!damagedCal.manualServoPending);
 cmd(damagedCal,"angle 31");steps(damagedCal,100);
 assert(damagedCal.robot.servoAngle==31&&!damagedCal.manualServoPending);
 cmd(damagedCal,"limits 119 31");assert(damagedCal.v(P_LIFT_LOW)==20);
 cmd(damagedCal,"limits 31 119");assert(damagedCal.v(P_LIFT_LOW)==31&&damagedCal.v(P_LIFT_HIGH)==119);
 cmd(damagedCal,"angle 119");steps(damagedCal,220);
 assert(damagedCal.robot.servoAngle==119&&!damagedCal.manualServoPending);
 cmd(damagedCal,"low");steps(damagedCal,220);
 assert(damagedCal.robot.servoAngle==31&&!damagedCal.manualServoPending);
 RobotHardware calibrated;calibrated.init();
 assert(calibrated.v(P_LIFT_LOW)==31&&calibrated.v(P_LIFT_HIGH)==119&&calibrated.lift.position==31);
 cmd(calibrated,"high");steps(calibrated,250);assert(calibrated.lift.position==119);
 assert(calibrated.v(P_LIFT_HIGH)==119);
 cmd(calibrated,"stream on");assert(calibrated.stream);
 cmd(calibrated,"stream off");assert(!calibrated.stream);
 puts("PASS: hardware adapter including independent persistent servo inversion, startup output, high/low mapping, detached confirmation, raised-fork lock and sensor-calibration erase/CRC independence");
}
