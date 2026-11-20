#include "RobotHardware.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
void cmd(RobotHardware &h,const char *s){char b[160];strcpy(b,s);h.handle(b,clockMs);}
void steps(RobotHardware &h,int count){for(int i=0;i<count;i++){clockMs+=10;h.tick();}}
void sample(RobotHardware &h,const char *name,int adc){for(int i=14;i<=16;i++)adcPins[i]=adc;cmd(h,name);steps(h,32);assert(!h.calibrating);}
int main(){
 for(int i=0;i<32;i++)inputPins[i]=HIGH;
 inputPins[2]=LOW; // HW-511 no reflective cargo, HIGH means cargo by default.
 RobotHardware h;h.init();assert(h.configError==0&&!h.armed&&!h.calibrationReady());
 assert(h.v(P_CONTACT_LOW)==0&&!h.contactPullup&&pinModes[2]==INPUT&&pinModes[17]==INPUT_PULLUP&&!h.contact());
 inputPins[2]=HIGH;assert(h.contact());inputPins[2]=LOW;assert(!h.contact());
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
 // A single ADC flicker must not swap black/white at the edge; a sustained
 // transition must be visible after two consecutive samples.
 for(int p=14;p<=16;p++)adcPins[p]=200;
 steps(restored,4);assert(restored.input.line[0]==1000);
 adcPins[14]=800;steps(restored,1);assert(restored.input.line[0]==1000);
 adcPins[14]=200;steps(restored,1);assert(restored.input.line[0]==1000);
 adcPins[14]=800;steps(restored,2);assert(restored.input.line[0]==0);
 adcPins[14]=200;steps(restored,3);assert(restored.input.line[0]==1000);
 // START: reject bouncing, arm after a long press and release, launch after
 // a second short press and release, abort motion on a confirmed press.
 RobotHardware start;start.init();
 inputPins[17]=LOW;steps(start,2);assert(!start.stableButton&&!start.armed);
 inputPins[17]=HIGH;steps(start,5);assert(!start.stableButton&&!start.armed);
 inputPins[17]=LOW;steps(start,5);assert(start.stableButton&&!start.armed);
 steps(start,205);assert(!start.armed);
 inputPins[17]=HIGH;steps(start,5);assert(start.armed&&start.robot.state==IDLE);
 inputPins[17]=LOW;steps(start,5);assert(start.robot.state==IDLE);
 inputPins[17]=HIGH;steps(start,5);assert(start.robot.active());
 inputPins[17]=LOW;steps(start,5);assert(start.robot.state==FAULT&&start.robot.fault==ABORTED&&!start.armed);
 inputPins[17]=HIGH;steps(start,5);assert(start.robot.state==FAULT&&!start.armed);
 cmd(h,"arm");cmd(h,"jog 100 -100 100");assert(h.jogging);steps(h,5);assert(outputPins[10]==100&&outputPins[11]==100);steps(h,6);assert(!h.jogging&&outputPins[10]==0&&outputPins[11]==0);
 // A 50 ms diagnostic pulse must reach its requested PWM on the first tick,
 // independently of the normal 5-per-10ms autonomous ramp and 70 minimum.
 cmd(h,"arm");cmd(h,"jog 255 -200 50");assert(h.jogging);steps(h,1);
 assert(outputPins[10]==255&&outputPins[11]==200&&outputPins[12]==HIGH&&outputPins[13]==LOW);
 steps(h,5);assert(!h.jogging&&outputPins[10]==0&&outputPins[11]==0);
 cmd(h,"arm");cmd(h,"jog 15 0 50");assert(h.jogging);steps(h,1);
 assert(outputPins[10]==15&&outputPins[11]==0);
 steps(h,5);assert(!h.jogging&&outputPins[10]==0&&outputPins[11]==0);
 cmd(h,"arm");cmd(h,"jog 0 0 100");assert(!h.jogging);
 // A two-stage diagnostic proves whether low PWM continues after an initial kick.
 // It bypasses ALL autonomous limits, trims, ramp, and crawl periods.
 cmd(h,"arm");cmd(h,"jogkick 20 -25 800 150 60");assert(h.jogging&&h.jogWithKick);
 steps(h,1);assert(outputPins[10]==150&&outputPins[11]==150);
 assert(outputPins[12]==HIGH&&outputPins[13]==LOW);
 steps(h,5);assert(h.jogging&&h.jogHoldLogged);
 assert(outputPins[10]==20&&outputPins[11]==25); // Hold never raised to minimum 70.
 steps(h,74);assert(!h.jogging&&outputPins[10]==0&&outputPins[11]==0);
 cmd(h,"jogkick 20 0 1000 145 60");assert(h.jogging); // Still armed.
 steps(h,1);assert(outputPins[10]==145);
 inputPins[h.v(P_START_PIN)]=LOW;steps(h,5);assert(!h.jogging&&!h.armed&&outputPins[10]==0);
 inputPins[h.v(P_START_PIN)]=HIGH;steps(h,5);
 cmd(h,"arm");cmd(h,"jogkick 20 0 100 145 100");assert(!h.jogging); // No hold phase.
 cmd(h,"jogkick 20 0 100 145 151");assert(!h.jogging);
 cmd(h,"jogkick 20 0 100 145");assert(!h.jogging);
 cmd(h,"jogkick 0 0 100 145 60");assert(!h.jogging);
 cmd(h,"jogkick -100 0 200 90 50");assert(h.jogging);
 steps(h,1);assert(outputPins[10]==100&&outputPins[12]==LOW); // Kick never reduces PWM.
 steps(h,20);assert(!h.jogging&&outputPins[10]==0);
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
 inputPins[h.v(P_CONTACT_PIN)]=HIGH;cmd(h,"arm");h.releaseButton(100,clockMs);assert(h.robot.state==IDLE);inputPins[h.v(P_CONTACT_PIN)]=LOW;
 h.releaseButton(100,clockMs);assert(h.robot.active());inputPins[h.v(P_START_PIN)]=LOW;steps(h,5);assert(h.robot.state==FAULT&&h.robot.fault==ABORTED&&outputPins[10]==0&&outputPins[11]==0);inputPins[h.v(P_START_PIN)]=HIGH;
 EEPROM.bytes[15]^=1;RobotHardware bad;bad.init();assert(!bad.calibrationReady());
 assert(h.v(P_DRIVER_MODE)==2&&h.v(P_CONTACT_PIN)==2&&h.v(P_LED_PIN)==255);
 h.outputMotors(90,-80);
 assert(outputPins[12]==HIGH&&outputPins[10]==90&&outputPins[13]==LOW&&outputPins[11]==80);
 // Reissuing the same request must not briefly zero the L298P PWM output.
 const int writesBefore=pwmWrites[10],zerosBefore=pwmZeroWrites[10];
 h.outputMotors(90,-80);
 assert(pwmWrites[10]==writesBefore&&pwmZeroWrites[10]==zerosBefore);
 h.outputMotors(100,-80);
 assert(pwmWrites[10]==writesBefore+1&&pwmZeroWrites[10]==zerosBefore);
 h.outputMotors(-100,-80); // A real direction change must still be safe.
 assert(outputPins[12]==LOW&&outputPins[10]==100&&pwmZeroWrites[10]==zerosBefore+1);
 h.outputMotors(0,0);assert(outputPins[10]==0&&outputPins[11]==0);
 // Tuned stall PWM preserves zero, sign and trim; out-of-range batches are atomic.
 RobotHardware tuned;tuned.init();
 cmd(tuned,"motor set 100 110 1200 900 130 120 95 100 135 125 8 12");
 assert(tuned.motorMinLeft==100&&tuned.motorMinRight==110&&tuned.v(P_DRIVE_PWM)==130);
 tuned.outputMotors(20,-30);assert(outputPins[10]==100&&outputPins[11]==110);
 tuned.outputMotors(0,0);
 // Motor trim/minimum affect driving, never the calibration probe.
 cmd(tuned,"arm");cmd(tuned,"jog 40 -45 50");assert(tuned.jogging);steps(tuned,1);
 assert(outputPins[10]==40&&outputPins[11]==45);
 assert(outputPins[12]==HIGH&&outputPins[13]==LOW);
 steps(tuned,5);assert(!tuned.jogging&&outputPins[10]==0&&outputPins[11]==0);assert(outputPins[10]==0&&outputPins[11]==0);
 tuned.outputMotors(-200,250);assert(outputPins[10]==240&&outputPins[11]==225);
 tuned.outputMotors(0,0);
 cmd(tuned,"motor set 5 5 1000 1000 0 120 95 100 135 125 8 12");assert(tuned.v(P_DRIVE_PWM)==130);
 cmd(tuned,"motor set 5 5 1000 1000 130 120 95 100 135 125 0 12");assert(tuned.motorMinLeft==100);
 // Optional start kick is applied once per motion, not on every crawl pulse.
 cmd(tuned,"motor dynamics 145 60 75 110 160 16");
 assert(tuned.motorKickPwm==145&&tuned.motorCrawlLimit==75);
 tuned.outputMotors(30,0);assert(outputPins[10]==145&&outputPins[11]==0);
 const int kickWrites=pwmWrites[10];
 tuned.outputMotors(30,0);assert(outputPins[10]==145&&pwmWrites[10]==kickWrites);
 clockMs+=70;
 tuned.outputMotors(30,0);
 const int onMs=36*160/110; // 30 * left trim 1.2
 assert(outputPins[10]==((clockMs%160)<(uint32_t)onMs?110:0));
 clockMs+=160; // No further kick on a repeated request.
 tuned.outputMotors(30,0);
 assert(outputPins[10]==((clockMs%160)<(uint32_t)onMs?110:0));
 tuned.outputMotors(0,0);assert(outputPins[10]==0);
 tuned.outputMotors(-30,0);assert(outputPins[10]==145&&outputPins[12]==LOW);
 tuned.outputMotors(30,0); // Direction reversal is not another kick.
 assert(outputPins[10]!=145);
 tuned.outputMotors(0,0);
 cmd(tuned,"arm");cmd(tuned,"jog 15 0 50");steps(tuned,1);
 assert(outputPins[10]==15);steps(tuned,5);assert(outputPins[10]==0);
 cmd(tuned,"motor dynamics 145 151 75 110 160 16");assert(tuned.motorKickMs==60);
 cmd(tuned,"motor dynamics 145 60 75 110 10 16");assert(tuned.motorCrawlPeriod==160);
 // Faster pulse schedules are accepted, with "on" still shorter than a cycle.
 cmd(tuned,"motor dynamics 145 60 75 110 40 8");
 assert(tuned.motorCrawlPeriod==40&&tuned.motorCrawlMinOn==8);
 cmd(tuned,"motor dynamics 145 60 75 110 30 30");
 assert(tuned.motorCrawlPeriod==40); // on duration must be < period
 cmd(tuned,"motor dynamics 145 60 75 110 160 16");
 assert(tuned.motorCrawlPeriod==160&&tuned.motorCrawlMinOn==16);
 cmd(tuned,"motor save");
 RobotHardware dynamicsBoot;dynamicsBoot.init();
 assert(dynamicsBoot.motorKickPwm==145&&dynamicsBoot.motorKickMs==60);
 assert(dynamicsBoot.motorCrawlLimit==75&&dynamicsBoot.motorCrawlPeriod==160);
 assert(dynamicsBoot.motorCrawlMinOn==16);
 // The optional 980..989 record has its own CRC and must not affect
 // existing motor trims (960..979) or servo limits (990..999).
 EEPROM.bytes[985]^=1;
 RobotHardware damagedDynamics;damagedDynamics.init();
 assert(damagedDynamics.motorKickPwm==0&&damagedDynamics.motorCrawlLimit==0);
 assert(damagedDynamics.motorMinLeft==100);
 cmd(tuned,"motor save");
 cmd(tuned,"motor save");
 RobotHardware persistedMotors;persistedMotors.init();
 assert(persistedMotors.motorMinLeft==100&&persistedMotors.motorMinRight==110);
 assert(persistedMotors.v(P_LEFT_TRIM)==1200&&persistedMotors.v(P_RAMP_STEP)==8);
 EEPROM.bytes[969]^=1;RobotHardware corruptedMotors;corruptedMotors.init();
 assert(corruptedMotors.motorMinLeft==70&&corruptedMotors.v(P_DRIVE_PWM)==85);
 cmd(tuned,"motor save");cmd(tuned,"motor clear");
 RobotHardware erasedMotors;erasedMotors.init();assert(erasedMotors.motorMinRight==70&&erasedMotors.v(P_DRIVE_PWM)==85);
 assert(erasedMotors.motorKickPwm==0&&erasedMotors.motorCrawlLimit==0);
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
 // Store both the logic level and optional pull-up independently from servo
 // direction and calibration. Fresh boards use HIGH with INPUT, not PULLUP.
 cmd(calibrated,"contact low");assert(calibrated.v(P_CONTACT_LOW)==1&&calibrated.contact());
 cmd(calibrated,"contact pullup on");assert(calibrated.contactPullup&&pinModes[2]==INPUT_PULLUP);
 RobotHardware contactBoot;contactBoot.init();
 assert(contactBoot.v(P_CONTACT_LOW)==1&&contactBoot.contactPullup&&pinModes[2]==INPUT_PULLUP);
 cmd(contactBoot,"contact high");cmd(contactBoot,"contact pullup off");
 assert(contactBoot.v(P_CONTACT_LOW)==0&&!contactBoot.contactPullup&&!contactBoot.contact()&&pinModes[2]==INPUT);
 RobotHardware contactBoot2;contactBoot2.init();
 assert(contactBoot2.v(P_CONTACT_LOW)==0&&!contactBoot2.contactPullup&&pinModes[2]==INPUT);
 puts("PASS: continuous motor PWM, median-filtered sensors, hardware adapter including independent persistent servo inversion, startup output, high/low mapping, detached confirmation, raised-fork lock and sensor-calibration erase/CRC independence, HW-511 modes and START debounce/hold/abort");
}
