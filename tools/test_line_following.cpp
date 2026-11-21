#include "RobotConfig.h"
#include "RadialCore.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>

// Deterministic host tests: real AVR and WASM both compile this same controller.
static SensorInput sample(uint16_t l,uint16_t c,uint16_t r){
 SensorInput s={{l,c,r},{false,false},false,false};return s;
}
int main(){
 // Configured distances are calibrated at stock PWM, not absolute wall time.
 // The effective speed model includes EEPROM minimum PWM and both motor trims.
 Settings timing;loadDefaultSettings(timing);
 RadialRobot timed;timed.init(timing,0);
 assert(timed.motionMs(510,85,85)==510);
 assert(timed.motionMs(800,55,55)==800);
 timing.v[P_TURN_PWM]=40;
 const uint32_t slow45=timed.pivotMs(timing.v[P_TURN45_MS]);
 assert(slow45>timing.v[P_TURN45_MS]);
 assert(slow45>=617&&slow45<=620); // Floor 70, not 40; Q8 precision.
 timed.enter(HUB_TURN,0);timed.turnSteps=1;
 const uint32_t turnDeadline=timing.v[P_SETTLE_MS]+timing.v[P_TURN_START_MS]+slow45;
 timed.tick(sample(0,0,0),turnDeadline-1);
 assert(timed.state==HUB_TURN);
 timed.tick(sample(0,0,0),turnDeadline);
 assert(timed.state==HUB_EXIT);
 // At the same effective motor drive, lowering the requested PWM must not
 // double the time. Higher or asymmetric minimums are also respected.
 timed.configureMotion(100,110);
 assert(timed.pivotMs(510)==510);
 timed.configureMotion(0,0);
 assert(timed.pivotMs(510)>1000);
 timed.configureMotion(70,70);
 timing.v[P_TURN_PWM]=40;
 timed.init(timing,0);timed.enter(UTURN,0);
 const uint32_t slowMin=timed.pivotMs(timing.v[P_UTURN_MIN_MS]);
 const uint32_t slowMax=timed.pivotMs(timing.v[P_UTURN_MAX_MS]);
 assert(slowMin>500&&slowMax>2800);
 const uint32_t settleSlow=timing.v[P_SETTLE_MS];
 timed.tick(sample(0,0,0),settleSlow+5);
 timed.tick(sample(0,0,0),settleSlow+55);
 assert(timed.turnGapSeen);
 timed.tick(sample(0,1000,0),settleSlow+slowMin+10);
 assert(timed.state==UTURN);
 timed.tick(sample(0,1000,0),settleSlow+slowMin+50);
 assert(timed.state==RETURN_HUB);
 // Delayed loop iterations do not stretch the configured PWM ramp or
 // skip the zero crossing when either wheel reverses.
 timed.init(timing,0);timed.drive(85,85);
 timed.services(35);assert(timed.left==15&&timed.right==15);
 timed.services(42);assert(timed.left==20&&timed.right==20);
 timed.drive(-85,85);
 timed.services(100);assert(timed.left==0&&timed.right==50);
 timed.services(110);assert(timed.left==-5&&timed.right==55);

 Settings settings;loadDefaultSettings(settings);
 RadialRobot robot;robot.init(settings,0);
 robot.follow(sample(0,1000,0),85,10);
 assert(robot.wantLeft==85&&robot.wantRight==85);
 robot.follow(sample(1000,0,0),85,20);
 assert(robot.wantLeft<robot.wantRight);  // Line on the left.
 assert(robot.wantLeft+robot.wantRight<170); // Adaptive speed reduction.
 assert(robot.lineDirection==-1);
 robot.follow(sample(0,0,0),85,30);
 assert(robot.state==IDLE&&robot.wantLeft==55&&robot.wantRight==55);
 robot.follow(sample(0,0,0),85,65);
 assert(robot.wantLeft==0&&robot.wantRight==55); // Search left.
 robot.follow(sample(0,1000,0),85,75);
 assert(robot.state==IDLE&&robot.wantLeft==85&&robot.wantRight==85);
 assert(robot.filteredDerivative==0); // No derivative kick on recovery.
 robot.follow(sample(1000,1000,1000),85,85);
 assert(robot.correction==0&&robot.wantLeft==85&&robot.wantRight==85);
 // A weak sighting on the other side must replace an earlier strong one.
 for(const bool lineOnLeft:{false,true}){
  robot.init(settings,0);
  robot.follow(lineOnLeft?sample(0,0,1000):sample(1000,0,0),85,10);
  robot.follow(lineOnLeft?sample(450,850,350):sample(350,850,450),85,20);
  robot.follow(sample(0,0,0),85,30);
  robot.follow(sample(0,0,0),85,65);
  assert(lineOnLeft?robot.wantLeft==0&&robot.wantRight>0:robot.wantRight==0&&robot.wantLeft>0);
 }
 // A centred sample provides no direction for searching through a gap.
 robot.init(settings,0);
 robot.follow(sample(0,0,1000),85,10);
 robot.follow(sample(0,1000,0),85,20);
 robot.follow(sample(0,0,0),85,30);
 robot.follow(sample(0,0,0),85,65);
 assert(robot.wantLeft==0&&robot.wantRight==0);
 // A short dropout must not postpone steering when an outer sensor sees the line again.
 robot.init(settings,0);
 robot.follow(sample(0,1000,0),85,10);
 robot.follow(sample(0,0,0),85,11);
 robot.follow(sample(1000,0,0),85,12);
 assert(robot.wantLeft<robot.wantRight&&robot.filteredDerivative==0);
 // A missing line is allowed only within the configured, bounded recovery time.
 robot.init(settings,0);
 robot.follow(sample(1000,0,0),85,95);
 robot.follow(sample(0,0,0),85,105);
 robot.follow(sample(0,0,0),85,105+settings.v[P_LOST_MS]);
 assert(robot.state==FAULT&&robot.fault==LINE_LOST);
 assert(robot.wantLeft==0&&robot.wantRight==0);
 // D filtering must damp a one-sample jump when proportional gain is disabled.
 settings.v[P_KP]=0;settings.v[P_KD]=100;settings.v[P_MAX_CORRECTION]=180;
 robot.init(settings,0);
 robot.follow(sample(0,1000,0),85,10);
 robot.follow(sample(0,0,1000),85,20);
 assert(robot.filteredDerivative==250);
 assert(robot.correction==25);
 // Two zero/minimum PWM floors must not erase every command difference
 // when cruise PWM is below approach PWM. Check both sides of a sharp bend.
 loadDefaultSettings(settings);robot.init(settings,0);
 robot.follow(sample(650,850,350),40,10);
 assert(robot.effectiveWheelPwm(robot.wantRight,1000,70)>70);
 robot.follow(sample(1000,0,0),40,20);
 assert(robot.wantLeft==0&&robot.wantRight>0);
 robot.follow(sample(0,0,1000),40,30);
 assert(robot.wantRight==0&&robot.wantLeft>0);
 // Normalize D by actual time between samples.
 settings.v[P_KP]=0;settings.v[P_KD]=100;settings.v[P_MAX_CORRECTION]=180;
 robot.init(settings,0);
 robot.follow(sample(0,1000,0),85,10);
 robot.follow(sample(0,0,1000),85,30);
 assert(robot.filteredDerivative==125);
 // With a load, base speed remains below unloaded speed even on the same bend.
 settings.v[P_KP]=110;settings.v[P_KD]=15;robot.init(settings,0);
 robot.follow(sample(0,1000,0),85,10);
 robot.follow(sample(0,500,500),85,20);
 const int unloaded=robot.wantLeft+robot.wantRight;
 robot.init(settings,0);
 robot.follow(sample(0,1000,0),75,10);
 robot.follow(sample(0,500,500),75,20);
 assert(robot.wantLeft+robot.wantRight<unloaded);

 // On the actual LDR strip the outer sensors may see half-black (~500)
 // while tracking. A painted crossing can raise them to ~700 without ever
 // reaching the previous fixed 800 threshold; still recognize the crossing.
 robot.init(settings,0);robot.enter(SEARCH_OUT,0);
 for(uint32_t t=130;t<=630;t+=10)robot.tick(sample(500,1000,500),t);
 assert(robot.state==SEARCH_OUT&&!robot.markerCandidateNow);
 robot.tick(sample(535,1000,550),640); // Side-edge jitter isn't a T-mark.
 assert(robot.state==SEARCH_OUT&&!robot.markerCandidateNow);
 robot.tick(sample(690,1000,715),650); // One noisy sample.
 assert(robot.markerCandidateNow&&robot.state==SEARCH_OUT);
 robot.tick(sample(500,1000,500),660);
 assert(!robot.markerCandidateNow&&robot.state==SEARCH_OUT);
 robot.tick(sample(690,1000,715),670);
 robot.tick(sample(690,1000,715),680);
 assert(robot.state==SEARCH_OUT);
 robot.tick(sample(690,1000,715),690);
 assert(robot.state==APPROACH); // Confirmed despite both sides < 800.

 // Confirm no false station event if the side LDRs are always dark: the
 // detector requires a change from each sensor's own normal baseline.
 robot.init(settings,0);robot.enter(SEARCH_OUT,0);
 for(uint32_t t=130;t<=750;t+=10)robot.tick(sample(750,1000,750),t);
 assert(robot.state==SEARCH_OUT&&!robot.markerCandidateNow);

 // Marker in the bridge uses the same contrast recognition and counts only
 // once while the vehicle remains above the transverse bar.
 robot.init(settings,0);robot.enter(BRIDGE,0);robot.crosses=1;
 for(uint32_t t=130;t<=190;t+=10)robot.tick(sample(500,1000,500),t);
 for(uint32_t t=200;t<=250;t+=10)robot.tick(sample(700,1000,730),t);
 assert(robot.crosses==0&&!robot.wideArmed);
 for(uint32_t t=260;t<=340;t+=10)robot.tick(sample(700,1000,730),t);
 assert(robot.crosses==0&&!robot.wideArmed);

 // The same transverse mark in the drop-off ray starts the delivery phase.
 robot.init(settings,0);robot.enter(DELIVERY_OUT,0);
 for(uint32_t t=130;t<=630;t+=10)robot.tick(sample(500,1000,500),t);
 robot.tick(sample(710,1000,720),640);
 robot.tick(sample(710,1000,720),650);
 robot.tick(sample(710,1000,720),660);
 assert(robot.state==DELIVERY_CREEP);

 // A slow default turn timer used to force a full 360-degree revolution.
 // Reacquire only after the old line has been absent and require a stable
 // centre crossing after the short anti-false-positive guard period.
 robot.init(settings,0);robot.enter(UTURN,0);
 const uint32_t settle=settings.v[P_SETTLE_MS];
 robot.tick(sample(0,1000,0),settle+10);
 assert(robot.state==UTURN&&!robot.turnGapSeen);
 robot.tick(sample(0,0,0),settle+50);
 robot.tick(sample(0,0,0),settle+100);
 assert(robot.turnGapSeen);
 robot.tick(sample(0,1000,0),settle+300);
 assert(robot.state==UTURN); // Too early, original line may still be visible.
 robot.tick(sample(0,0,0),settle+350);
 robot.tick(sample(0,1000,0),settle+900);
 assert(robot.state==UTURN);
 robot.tick(sample(0,1000,0),settle+935);
 assert(robot.state==RETURN_HUB&&robot.wantLeft==0&&robot.wantRight==0);
 assert(robot.left==0&&robot.right==0); // No coasting past 180 degrees.

 // Seeing black at an outer detector is not departure from the old line.
 robot.init(settings,0);robot.enter(UTURN,0);
 robot.tick(sample(1000,0,0),settle+50);
 robot.tick(sample(1000,0,0),settle+100);
 assert(!robot.turnGapSeen);
 robot.tick(sample(0,0,0),settle+110);
 robot.tick(sample(0,0,0),settle+160);
 assert(robot.turnGapSeen);
 // Even if the confirmation completes after the earliest admissible time,
 // an earlier crossing began too soon and must stop instead of adding a lap.
 robot.tick(sample(0,1000,0),settle+480);
 assert(robot.wantLeft==-settings.v[P_APPROACH_PWM]);
 robot.tick(sample(0,1000,0),settle+520);
 assert(robot.state==FAULT&&robot.fault==TURN_EARLY&&robot.left==0&&robot.right==0);

 // A false one-frame line sighting does not complete the U-turn.
 robot.init(settings,0);robot.enter(UTURN,0);
 robot.tick(sample(0,0,0),settle+10);
 robot.tick(sample(0,0,0),settle+60);
 robot.tick(sample(0,1000,0),settle+950);
 robot.tick(sample(0,0,0),settle+960);
 assert(robot.state==UTURN);
 robot.tick(sample(0,1000,0),settle+1000);
 robot.tick(sample(0,1000,0),settle+1040);
 assert(robot.state==RETURN_HUB);

 // A turn without line departure is NOT a confirmed 180, even if the
 // timer has elapsed. Fail safely at the timeout rather than spin forever.
 robot.init(settings,0);robot.enter(UTURN,0);
 robot.tick(sample(0,1000,0),settle+1000);
 assert(robot.state==UTURN&&!robot.turnGapSeen);
 robot.tick(sample(0,1000,0),settle+settings.v[P_UTURN_MAX_MS]+1);
 assert(robot.state==FAULT&&robot.fault==TURN_TIMEOUT);
 robot.init(settings,0);robot.loaded=true;robot.enter(UTURN,0);
 robot.tick(sample(0,0,0),settle+10);
 robot.tick(sample(0,0,0),settle+60);
 robot.tick(sample(0,1000,0),settle+settings.v[P_UTURN_LOADED_MIN_MS]+15);
 robot.tick(sample(0,1000,0),settle+settings.v[P_UTURN_LOADED_MIN_MS]+55);
 assert(robot.state==RETURN_HUB);

 // Limit forward-wheel differential to avoid stalling the inner TT motor
 // at an edge while preserving correct steering direction.
 robot.init(settings,0);
 robot.follow(sample(1000,0,0),85,10);
 assert(robot.wantLeft>=settings.v[P_APPROACH_PWM]&&robot.wantRight>=settings.v[P_APPROACH_PWM]);

 // At low cruise speed the inner wheel minimum can overpower the
 // requested heading. Check the applied, trim-normalized PWM in both directions.
 for(const bool lineOnLeft:{false,true}){
  const uint16_t innerTrim=1200,outerTrim=900;
  settings.v[P_LEFT_TRIM]=lineOnLeft?innerTrim:outerTrim;
  settings.v[P_RIGHT_TRIM]=lineOnLeft?outerTrim:innerTrim;
  robot.configureMotion(lineOnLeft?120:65,lineOnLeft?65:120);
  robot.init(settings,0);
  robot.follow(lineOnLeft?sample(700,650,0):sample(0,650,700),60,10);
  const uint16_t inner=robot.effectiveWheelPwm(lineOnLeft?robot.wantLeft:robot.wantRight,innerTrim,120);
  const uint16_t outer=robot.effectiveWheelPwm(lineOnLeft?robot.wantRight:robot.wantLeft,outerTrim,65);
  assert((uint32_t)outer*innerTrim>(uint32_t)inner*outerTrim);
 }
 loadDefaultSettings(settings);
 robot.configureMotion(70,70);

 // Sensor-guided exit from the hub, while retaining the calibrated exit timer.
 robot.init(settings,0);robot.enter(HUB_EXIT,0);
 robot.tick(sample(1000,0,0),455);
 assert(robot.state==HUB_EXIT&&robot.wantLeft<robot.wantRight);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+settings.v[P_HUB_EXIT_MS]);
 assert(robot.state==ACQUIRE&&robot.wantLeft==0&&robot.wantRight==0);
 // Sweep equal distances around the starting heading within one search budget.
 for(const int direction:{-1,1}){
  robot.init(settings,0);robot.enter(ACQUIRE,0);robot.turnSteps=direction;
  const uint32_t settle=settings.v[P_SETTLE_MS],budget=settings.v[P_ACQUIRE_MS];
  int first=0,sweepBack=0;
  for(uint32_t t=0;t<budget;t++){
   robot.tick(sample(0,0,0),settle+t);
   if(t<120)assert(robot.wantLeft==55&&robot.wantRight==55);
   else if(robot.wantLeft==-55*direction)first++;
   else if(robot.wantLeft==55*direction)sweepBack++;
  }
  assert(first==(budget-120)/3);
  assert(sweepBack-first>=first&&sweepBack-first<=first+2);
  robot.tick(sample(0,0,0),settle+budget);
  assert(robot.state==FAULT&&robot.fault==EXIT_TIMEOUT&&robot.wantLeft==0&&robot.wantRight==0);
 }
 // Approach and retreat keep a matched profile even after picking up cargo.
 Settings lowSpeed;loadDefaultSettings(lowSpeed);
 lowSpeed.v[P_DRIVE_PWM]=35;lowSpeed.v[P_LOADED_PWM]=30;
 RadialRobot slowRobot;slowRobot.init(lowSpeed,0);slowRobot.configureMotion(0,0);
 const uint32_t settleLow=lowSpeed.v[P_SETTLE_MS];
 slowRobot.enter(APPROACH,0);
 uint32_t search=slowRobot.approachMs(slowRobot.z(Z_SEARCH_MS),35);
 slowRobot.tick(sample(0,1000,0),settleLow+search-1);
 assert(slowRobot.state==APPROACH&&slowRobot.wantLeft==35&&slowRobot.wantRight==35);
 slowRobot.tick(sample(0,1000,0),settleLow+search);
 assert(slowRobot.state==RETREAT);
 slowRobot.loaded=true;
 const uint32_t retreat=slowRobot.entered;
 slowRobot.tick(sample(0,1000,0),retreat+settleLow+slowRobot.retreatDuration-1);
 assert(slowRobot.state==RETREAT&&slowRobot.wantLeft==-35&&slowRobot.wantRight==-35);
 slowRobot.tick(sample(0,1000,0),retreat+settleLow+slowRobot.retreatDuration);
 assert(slowRobot.state==UTURN);
 slowRobot.init(lowSpeed,0);slowRobot.enter(DROP_BACK,0);
 slowRobot.tick(sample(0,1000,0),settleLow+20);
 assert(slowRobot.wantLeft==-30&&slowRobot.wantRight==-30);
 // Ignore a single-line spike and the hub's own optical signature.
 robot.init(settings,0);robot.enter(ACQUIRE,0);
 SensorInput hub=sample(500,500,500);hub.hub[0]=true;
 robot.tick(hub,settings.v[P_SETTLE_MS]+10);assert(robot.state==ACQUIRE);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+40);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+50);
 robot.tick(sample(1000,0,0),settings.v[P_SETTLE_MS]+55);
 robot.tick(sample(1000,0,0),settings.v[P_SETTLE_MS]+87);
 assert(robot.state==ACQUIRE&&robot.wantLeft<robot.wantRight);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+90);
 assert(robot.state==ACQUIRE);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+90+settings.v[P_TURN_LINE_MS]+1);
 assert(robot.state==SEARCH_OUT);
 // Different reflected-light amplitudes and modest sensor jitter must not
 // change the direction of a genuine curve after calibration.
 robot.init(settings,0);
 robot.follow(sample(0,650,0),85,10);
 for(int i=0;i<10;i++){
  int k=650+(i%3)*100;
  robot.follow(sample(k,220,0),85,(uint32_t)(20+i*10));
  assert(robot.wantLeft<robot.wantRight&&robot.state==IDLE);
 }
 robot.follow(sample(0,250,700),85,130);
 assert(robot.wantLeft>robot.wantRight);
 // One failed-to-detect sensor still leaves the controller bounded; a totally
 // dark/disconnected line bank must stop after LOST_MS, never drive forever.
 robot.init(settings,0);
 for(int i=1;i<=8;i++)robot.follow(sample(0,750,150+(i%2)*40),85,(uint32_t)i*10);
 assert(robot.state==IDLE);
 robot.follow(sample(0,0,0),85,100);
 robot.follow(sample(0,0,0),85,100+settings.v[P_LOST_MS]);
 assert(robot.state==FAULT&&robot.fault==LINE_LOST);
 std::puts("PASS: adaptive crossbar/zone/bridge detection, tracking, gentle steering, gap-confirmed 180 U-turn, filtered D, hub exit, timed ray acquisition, light fluctuations and sensor dropout");
}
