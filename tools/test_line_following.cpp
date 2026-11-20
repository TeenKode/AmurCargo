#include "RobotConfig.h"
#include "RadialCore.h"
#include <cassert>
#include <cstdio>

// Deterministic host tests: real AVR and WASM both compile this same controller.
static SensorInput sample(uint16_t l,uint16_t c,uint16_t r){
 SensorInput s={{l,c,r},{false,false},false,false};return s;
}
int main(){
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
 // A missing line is allowed only within the configured, bounded recovery time.
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

 // Sensor-guided exit from the hub, while retaining the calibrated exit timer.
 robot.init(settings,0);robot.enter(HUB_EXIT,0);
 robot.tick(sample(1000,0,0),455);
 assert(robot.state==HUB_EXIT&&robot.wantLeft<robot.wantRight);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+settings.v[P_HUB_EXIT_MS]);
 assert(robot.state==ACQUIRE&&robot.wantLeft==0&&robot.wantRight==0);
 // An uncertain turn must never cause prolonged full-speed blind driving.
 robot.init(settings,0);robot.enter(ACQUIRE,0);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+5);
 assert(robot.wantLeft==55&&robot.wantRight==55);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+135);
 assert(robot.wantLeft==-55&&robot.wantRight==55);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+settings.v[P_ACQUIRE_MS]/2+10);
 assert(robot.wantLeft==55&&robot.wantRight==-55);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+settings.v[P_ACQUIRE_MS]+1);
 assert(robot.state==FAULT&&robot.fault==EXIT_TIMEOUT&&robot.wantLeft==0&&robot.wantRight==0);
 // Ignore a single-line spike and the hub's own optical signature.
 robot.init(settings,0);robot.enter(ACQUIRE,0);
 SensorInput hub=sample(500,500,500);hub.hub[0]=true;
 robot.tick(hub,settings.v[P_SETTLE_MS]+10);assert(robot.state==ACQUIRE);
 robot.tick(sample(0,1000,0),settings.v[P_SETTLE_MS]+40);
 robot.tick(sample(0,0,0),settings.v[P_SETTLE_MS]+50);
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
