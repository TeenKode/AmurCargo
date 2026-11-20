#pragma once
#include "Settings.h"

// Portable navigation engine: the same file is compiled for ATmega328P and WebAssembly.
enum RobotState { IDLE,HUB_TURN,HUB_EXIT,ACQUIRE,SEARCH_OUT,APPROACH,LIFT,RETREAT,UTURN,RETURN_HUB,HUB_CENTRE,BRIDGE,DELIVERY_OUT,DELIVERY_CREEP,LOWER,DROP_BACK,DONE,FAULT };
enum RobotFault { OK=0,BAD_SETTINGS=1,NO_CARGO=2,LINE_LOST=3,STATION_TIMEOUT=4,HUB_TIMEOUT=5,TURN_TIMEOUT=6,EXIT_TIMEOUT=7,LOAD_LOST=8,CARGO_STUCK=9,ABORTED=10,MISSION_TIMEOUT=11,SERVO_TIMEOUT=12 };
enum LegPurpose { SEARCH_LEG,BRIDGE_LEG,DELIVERY_LEG };
struct SensorInput { uint16_t line[3]; bool hub[2]; bool contact; bool abort; };
struct HoldTimer {
 uint32_t since; bool active;
 void clear(){active=false;since=0;}
 bool test(bool condition,uint32_t now,uint16_t duration){if(!condition){clear();return false;}if(!active){active=true;since=now;}return (uint32_t)(now-since)>=duration;}
};
inline int16_t clamp16(int32_t x,int16_t lo,int16_t hi){return x<lo?lo:x>hi?hi:(int16_t)x;}
inline uint16_t max3(uint16_t a,uint16_t b,uint16_t c){return a>b?(a>c?a:c):(b>c?b:c);}
inline uint16_t abs16(int16_t x){return x<0?(uint16_t)-x:(uint16_t)x;}

struct RadialRobot {
 const Settings *cfg;
 RobotState state;RobotFault fault;LegPurpose purpose;
 uint8_t hub,heading,ray,searchPos,expectedHub,crosses;
 bool loaded,wideArmed;
 // Estimates actual wheel drive for timed manoeuvres. Updated from EEPROM motor tuning.
 uint8_t minMotorLeft=70,minMotorRight=70,crawlLimit=0,crawlPwm=110,crawlPeriod=160,crawlMinOn=16;
 int8_t turnSteps;
 int16_t left,right,wantLeft,wantRight,correction,previousError,filteredDerivative;
 int8_t lineDirection;bool resetDerivative;
 uint8_t servoAngle,servoGoal;
 uint32_t entered,started,lastMotor,lastServo,lastLine,approachUsed,retreatDuration;
 HoldTimer contactTimer,wideTimer,clearTimer,lineTimer,hubTimer,lostTimer,heldTimer,servoTimer,turnGapTimer;
 bool turnGapSeen;
 // Side LDR reference on the current ray, reset after changing robot state.
 uint16_t markerBaseLeft,markerBaseRight;
 int16_t markerRiseLeft,markerRiseRight;
 uint32_t lastMarkerSample;
 bool markerBaseReady,markerCandidateNow;
 uint16_t v(Param p)const{return cfg->v[p];}
 uint16_t z(ZoneParam p)const{return cfg->zone[hub][ray][p];}
 void configureMotion(uint8_t leftMinimum,uint8_t rightMinimum,uint8_t limit,uint8_t pulsePwm,uint8_t period,uint8_t minOn){
  minMotorLeft=leftMinimum;minMotorRight=rightMinimum;
  crawlLimit=limit;crawlPwm=pulsePwm;crawlPeriod=period;crawlMinOn=minOn;
 }
 // Relative PWM is only an estimate of wheel speed, not encoder feedback.
 // Account for trim, motor minimum, and the average on-time of crawl pulses.
 uint16_t effectiveWheelPwm(uint16_t command,uint16_t trim,uint8_t minimum)const{
  if(!command)return 0;
  uint32_t power=(uint32_t)command*trim/1000UL;
  if(power>255)power=255;
  if(crawlLimit&&power<crawlLimit&&crawlPwm&&crawlPeriod>1){
   uint32_t on=power*crawlPeriod/crawlPwm;
   if(on<crawlMinOn)on=crawlMinOn;
   if(on>=crawlPeriod)on=crawlPeriod-1;
   return (uint16_t)(on*crawlPwm/crawlPeriod);
  }
  return (uint16_t)(power<minimum?minimum:power);
 }
 uint16_t effectiveMotionPwm(uint16_t command)const{
  uint16_t l=effectiveWheelPwm(command,v(P_LEFT_TRIM),minMotorLeft);
  uint16_t r=effectiveWheelPwm(command,v(P_RIGHT_TRIM),minMotorRight);
  return (uint16_t)((l+r)/2);
 }
 // Times in configuration describe travel at the original default PWM.
 // Keep sensor debounces/settle and the mission watchdog in wall-clock time.
 uint32_t motionMs(uint32_t calibratedMs,uint16_t command,uint16_t reference)const{
  if(!calibratedMs)return 0;
  const uint16_t actual=effectiveMotionPwm(command),baseline=effectiveMotionPwm(reference);
  if(!actual||!baseline)return calibratedMs;
  return (calibratedMs*(uint32_t)baseline+actual/2)/actual;
 }
 uint32_t cruiseMs(uint32_t calibratedMs)const{
  return motionMs(calibratedMs,loaded?v(P_LOADED_PWM):v(P_DRIVE_PWM),loaded?75:85);
 }
 uint32_t slowMs(uint32_t calibratedMs)const{return motionMs(calibratedMs,v(P_APPROACH_PWM),55);}
 uint32_t centreMs(uint32_t calibratedMs)const{return motionMs(calibratedMs,v(P_CENTRE_PWM),80);}
 uint32_t pivotMs(uint32_t calibratedMs)const{
  return motionMs(calibratedMs,loaded?v(P_TURN_LOADED_PWM):v(P_TURN_PWM),loaded?75:85);
 }
 bool active()const{return state!=IDLE&&state!=DONE&&state!=FAULT;}
 void stop(){left=right=wantLeft=wantRight=0;}
 void drive(int16_t l,int16_t r){wantLeft=clamp16(l,-255,255);wantRight=clamp16(r,-255,255);}
 void enter(RobotState next,uint32_t now){
  stop();state=next;entered=now;correction=previousError=filteredDerivative=0;lineDirection=0;resetDerivative=true;lastLine=now;
  wideTimer.clear();clearTimer.clear();lineTimer.clear();hubTimer.clear();lostTimer.clear();servoTimer.clear();turnGapTimer.clear();turnGapSeen=false;
  markerBaseLeft=markerBaseRight=0;markerRiseLeft=markerRiseRight=0;lastMarkerSample=now;markerBaseReady=markerCandidateNow=false;
 }
 void fail(RobotFault why,uint32_t now){fault=why;servoGoal=servoAngle;enter(FAULT,now);}
 void init(const Settings &settings,uint32_t now=0){
  cfg=&settings;state=IDLE;fault=OK;purpose=SEARCH_LEG;hub=(uint8_t)v(P_START_HUB);heading=(uint8_t)v(P_START_HEADING);ray=searchPos=expectedHub=crosses=0;
  loaded=false;wideArmed=true;turnSteps=0;stop();correction=previousError=0;servoAngle=servoGoal=(uint8_t)v(P_LIFT_LOW);
  entered=started=lastMotor=lastServo=lastLine=now;approachUsed=retreatDuration=0;filteredDerivative=0;lineDirection=0;resetDerivative=true;
  contactTimer.clear();wideTimer.clear();clearTimer.clear();lineTimer.clear();hubTimer.clear();lostTimer.clear();heldTimer.clear();servoTimer.clear();turnGapTimer.clear();turnGapSeen=false;
  markerBaseLeft=markerBaseRight=0;markerRiseLeft=markerRiseRight=0;lastMarkerSample=now;markerBaseReady=markerCandidateNow=false;
 }
 void plan(uint32_t now){
  if(hub==v(P_START_HUB)){
   if(loaded){purpose=BRIDGE_LEG;ray=bridgeRay(hub);}
   else {if(searchPos>=cfg->searchCount){fail(NO_CARGO,now);return;}purpose=SEARCH_LEG;ray=cfg->search[searchPos];}
  }else{purpose=DELIVERY_LEG;ray=(uint8_t)v(P_DROP_RAY);}
  int8_t d=(int8_t)((ray+8-heading)%8);if(d>4)d-=8;turnSteps=d;enter(HUB_TURN,now);
 }
 bool start(uint32_t now){
  if(state!=IDLE||loaded||servoAngle!=v(P_LIFT_LOW))return false;
  if(settingsError(*cfg)){fail(BAD_SETTINGS,now);return false;}
  fault=OK;hub=(uint8_t)v(P_START_HUB);heading=(uint8_t)v(P_START_HEADING);searchPos=0;loaded=false;started=now;approachUsed=0;plan(now);return true;
 }
 int16_t ramp(int16_t actual,int16_t target){
  if(actual&&((actual>0)!=(target>0)))target=0;
  int16_t step=(int16_t)v(P_RAMP_STEP);return actual<target?(actual+step>target?target:actual+step):(actual-step<target?target:actual-step);
 }
 void services(uint32_t now){
  if((uint32_t)(now-lastMotor)>=v(P_RAMP_MS)){lastMotor=now;left=ramp(left,wantLeft);right=ramp(right,wantRight);}
  if(servoAngle!=servoGoal&&(uint32_t)(now-lastServo)>=v(P_SERVO_MS)){
   lastServo=now;int16_t a=servoAngle,step=v(P_SERVO_STEP);a+=servoGoal>a?step:-step;
   if((servoGoal>servoAngle&&a>servoGoal)||(servoGoal<servoAngle&&a<servoGoal))a=servoGoal;servoAngle=(uint8_t)a;
  }
 }
 bool narrow(const SensorInput &s)const{return max3(s.line[0],s.line[1],s.line[2])>=v(P_LINE_THRESHOLD)&&!wide(s);}
 bool wide(const SensorInput &s)const{return s.line[0]>=v(P_WIDE_THRESHOLD)&&s.line[1]>=v(P_WIDE_THRESHOLD)&&s.line[2]>=v(P_WIDE_THRESHOLD);}
 // Perpendicular stripe raises BOTH lateral LDRs above their usual levels
 // on this ray. A fixed 800/1000 on every sensor misses partial black bars.
 // Process once per SENSOR_MS, never at each high-frequency hardware tick.
 bool crossbar(const SensorInput &s,uint32_t now){
  if((uint32_t)(now-lastMarkerSample)<v(P_SENSOR_MS))return markerCandidateNow;
  lastMarkerSample=now;
  const uint16_t l=s.line[0],r=s.line[2];
  if(!markerBaseReady){
   markerBaseLeft=l;markerBaseRight=r;markerBaseReady=true;
   markerRiseLeft=markerRiseRight=0;markerCandidateNow=false;return false;
  }
  markerRiseLeft=(int16_t)l-(int16_t)markerBaseLeft;
  markerRiseRight=(int16_t)r-(int16_t)markerBaseRight;
  // WIDE_THRESHOLD remains the UI sensitivity control. Defaults 800/350
  // require a rise of 90 on each side and 270 total.
  uint16_t contrast=(v(P_WIDE_THRESHOLD)-v(P_LINE_THRESHOLD))/5;
  if(contrast<65)contrast=65;
  markerCandidateNow=s.line[1]>=v(P_LINE_THRESHOLD) &&
     l>=v(P_LINE_THRESHOLD)&&r>=v(P_LINE_THRESHOLD) &&
     markerRiseLeft>=(int16_t)contrast &&
     markerRiseRight>=(int16_t)contrast &&
     (int32_t)markerRiseLeft+markerRiseRight>=3*(int32_t)contrast;
  if(!markerCandidateNow){
   // Don't learn the crossbar while it is being confirmed. Adapt slowly to
   // illumination changes instead of following every flicker near the edge.
   markerBaseLeft=(uint16_t)(((uint32_t)markerBaseLeft*15+l+8)/16);
   markerBaseRight=(uint16_t)(((uint32_t)markerBaseRight*15+r+8)/16);
  }
  return markerCandidateNow;
 }
 // Follow the line using a filtered PD term and a speed schedule that slows down when off-centre.
 // The same controller runs on AVR hardware and in the WASM simulator.
 void follow(const SensorInput &s,int16_t pwm,uint32_t now){
  const bool onLine=max3(s.line[0],s.line[1],s.line[2])>=v(P_LINE_THRESHOLD);
  if(!onLine){
   resetDerivative=true;
   // LOST_MS is a hard limit for a cautious search, not an invitation to drive blindly.
   if(lostTimer.test(true,now,v(P_LOST_MS))){fail(LINE_LOST,now);return;}
   uint32_t missing=(uint32_t)(now-lostTimer.since);
   int16_t recovery=(int16_t)v(P_APPROACH_PWM);
   if(recovery>pwm)recovery=pwm;
   // Cross a tiny sensor dropout slowly; then arc toward the last confirmed side.
   if(missing<30)drive(recovery,recovery);
   else if(lineDirection>0)drive(recovery,0);
   else if(lineDirection<0)drive(0,recovery);
   else drive(0,0);
   return;
  }
  if(lostTimer.active)resetDerivative=true;
  lostTimer.clear();
  if((uint32_t)(now-lastLine)>=v(P_SENSOR_MS)){
   lastLine=now;
   const bool marker=wide(s);
   uint32_t sum=(uint32_t)s.line[0]+s.line[1]+s.line[2];
   int16_t error=sum?(int16_t)(((int32_t)s.line[2]-s.line[0])*1000L/(int32_t)sum):0;
   // Ignore tiny left/right differences near the centre rather than hunting them.
   if(abs16(error)<=25)error=0;
   if(marker){correction=0;filteredDerivative=0;lineDirection=0;}
   else {
    if(error>80)lineDirection=1;
    else if(error< -80)lineDirection=-1;
    // Filter derivative over four samples; discard the transient on reacquisition.
    int16_t delta=resetDerivative?0:(int16_t)(error-previousError);
    filteredDerivative=resetDerivative?0:(int16_t)(((int32_t)filteredDerivative*3+delta)/4);
    correction=clamp16(((int32_t)v(P_KP)*error+(int32_t)v(P_KD)*filteredDerivative)/1000L,-(int16_t)v(P_MAX_CORRECTION),(int16_t)v(P_MAX_CORRECTION));
   }
   previousError=error;resetDerivative=false;
   // Slow progressively as the line moves toward an outer sensor. Never speed up in a turn.
   // Do not command a wheel below the cautious forward-drive PWM while
   // tracking. With TT motors + L298P this previously stalled the inside
   // wheel, turning small errors into violent alternating pivots.
   int16_t floor=(int16_t)v(P_APPROACH_PWM);
   if(floor>pwm)floor=pwm;
   int16_t magnitude=(int16_t)abs16(error);
   if(magnitude>1000)magnitude=1000;
   // Modest corner slowdown keeps steering authority even at the outer sensor.
   int16_t base=marker?pwm:(int16_t)(pwm-(int32_t)(pwm-floor)*magnitude/3000L);
   int16_t steerLimit=base-floor;
   int16_t steer=clamp16(correction,-steerLimit,steerLimit);
   drive(clamp16(base+steer,0,255),clamp16(base-steer,0,255));
   return;
  }
  // Reuse the last motor request between scheduled sensor updates.
 }
 void pickup(uint32_t now,uint32_t used){approachUsed=used;servoGoal=(uint8_t)v(P_LIFT_HIGH);enter(LIFT,now);}
 void beginRetreat(uint32_t now){retreatDuration=slowMs(z(Z_BACKOFF_MS))+approachUsed*v(P_REVERSE_RATIO)/1000UL;enter(RETREAT,now);}
 bool servoDone(uint32_t now){return servoTimer.test(servoAngle==servoGoal,now,v(P_SERVO_SETTLE_MS));}
 void tick(const SensorInput &s,uint32_t now){
  bool contact=contactTimer.test(s.contact,now,v(P_CONTACT_MS));
  if(s.abort&&active()){fail(ABORTED,now);return;}
  if(active()&&(uint32_t)(now-started)>(uint32_t)v(P_MISSION_SECONDS)*1000UL){fail(MISSION_TIMEOUT,now);return;}
  if(active()&&loaded&&v(P_CHECK_HELD_CONTACT)&&state!=LOWER&&state!=DROP_BACK){if(heldTimer.test(!s.contact,now,v(P_HELD_LOST_MS))){fail(LOAD_LOST,now);return;}}else heldTimer.clear();
  if(state==IDLE||state==DONE||state==FAULT){stop();services(now);return;}
  uint32_t elapsed=now-entered,settle=v(P_SETTLE_MS),e=elapsed>=settle?elapsed-settle:0;
  if(state==LIFT||state==LOWER){
   if(servoDone(now)){
    if(state==LIFT){loaded=true;beginRetreat(now);}else{loaded=false;enter(DROP_BACK,now);}
   }else{
    uint32_t maxServo=((uint32_t)180*v(P_SERVO_MS)/v(P_SERVO_STEP))+v(P_SERVO_SETTLE_MS)+1500UL;
    if(elapsed>maxServo)fail(SERVO_TIMEOUT,now);
   }services(now);return;
  }
  if(elapsed<settle){drive(0,0);services(now);return;}
  const int16_t cruise=loaded?v(P_LOADED_PWM):v(P_DRIVE_PWM),slow=v(P_APPROACH_PWM),turn=loaded?v(P_TURN_LOADED_PWM):v(P_TURN_PWM);
  switch(state){
   case HUB_TURN:{
    if(!turnSteps){heading=ray;enter(HUB_EXIT,now);break;}
    uint32_t duration=v(P_TURN_START_MS)+pivotMs((uint32_t)abs16(turnSteps)*(loaded?v(P_TURN45_LOADED_MS):v(P_TURN45_MS));
    if(turnSteps<0)duration=duration*v(P_TURN_RIGHT_SCALE)/1000UL;
    if(e>=duration){heading=ray;enter(HUB_EXIT,now);}else drive(turnSteps>0?-turn:turn,turnSteps>0?turn:-turn);break;
   }
   case HUB_EXIT:{
    // The turn angle is predicted from time, but steer by a confirmed ray as soon
    // as the robot's forward sensor has cleared the hub. Keep the original exit
    // distance budget so station/bridge timing remains comparable.
    if(e>=cruiseMs(v(P_HUB_EXIT_MS))){enter(ACQUIRE,now);break;}
    if(e>=cruiseMs(v(P_HUB_EXIT_MS))/2&&narrow(s)&&!s.hub[hub])follow(s,cruise,now);
    else drive(cruise,cruise);
    break;
   }
   case ACQUIRE:{
    // A timed hub turn is not evidence that the correct ray was reached.
    // Only a narrow line, continuously observed for TURN_LINE_MS, confirms it.
    bool line=narrow(s)&&!s.hub[hub];
    if(lineTimer.test(line,now,v(P_TURN_LINE_MS))){crosses=(uint8_t)v(P_BRIDGE_CROSSES);wideArmed=true;enter(purpose==SEARCH_LEG?SEARCH_OUT:purpose==BRIDGE_LEG?BRIDGE:DELIVERY_OUT,now);}
    else if(e>slowMs(v(P_ACQUIRE_MS)))fail(EXIT_TIMEOUT,now);
    else if(line)follow(s,cruise,now);
    else {
     // Never continue at full cruise into an unobserved ray. A brief forward
     // creep lets the sensor clear the hub, then a bounded two-sided scan.
     // TURN_STEPS biases the first scan toward the last predicted turn.
     int16_t scan=(int16_t)v(P_APPROACH_PWM);
     if(scan>cruise)scan=cruise;
     if(e<120)drive(scan,scan);
     else {
      bool first=e<slowMs(v(P_ACQUIRE_MS))/2;
      int8_t side=turnSteps<0?-1:1;
      if(!first)side=-side;
      drive(side>0?-scan:scan,side>0?scan:-scan);
     }
    }
    break;
   }
   case SEARCH_OUT:case DELIVERY_OUT:{
    if(state==SEARCH_OUT&&e>=cruiseMs(z(Z_OUT_MIN_MS))&&contact){pickup(now,0);break;}
    const bool marker=crossbar(s,now);
    if(wideTimer.test(e>=cruiseMs(z(Z_OUT_MIN_MS))&&marker,now,v(P_MARKER_MS))){
     enter(state==SEARCH_OUT?APPROACH:DELIVERY_CREEP,now);break;
    }
    if(e>cruiseMs(z(Z_OUT_MAX_MS))){fail(STATION_TIMEOUT,now);break;}
    // Reduce speed while confirming the bar, so a short mark isn't missed.
    if(marker&&e>=cruiseMs(z(Z_OUT_MIN_MS)))drive(slow,slow);
    else follow(s,cruise,now);
    break;
   }
   case APPROACH:
    if(contact){pickup(now,e);break;}
    if(e>=slowMs(z(Z_SEARCH_MS))){approachUsed=e;beginRetreat(now);}else drive(slow,slow);break;
   case RETREAT:
    if(e>=retreatDuration)enter(UTURN,now);else drive(-slow,-slow);break;
   case UTURN:{
    const uint32_t minMs=pivotMs(loaded?v(P_UTURN_LOADED_MIN_MS):v(P_UTURN_MIN_MS));
    const uint32_t maxMs=pivotMs(loaded?v(P_UTURN_LOADED_MAX_MS):v(P_UTURN_MAX_MS));
    const bool onCentre=s.line[1]>=v(P_LINE_THRESHOLD)&&!wide(s);
    // A timed minimum of 2050 ms could rotate a real TT chassis through a
    // full 360 degrees before the old code was even allowed to see the line.
    // First confirm we have LEFT the original line, then stop at the next
    // stable centre-line crossing (nominally 180 degrees).
    if(!turnGapSeen && turnGapTimer.test(!onCentre,now,40)){
     turnGapSeen=true;lineTimer.clear();
    }
    if(turnGapSeen && lineTimer.test(e>=minMs&&onCentre&&narrow(s),now,v(P_TURN_LINE_MS))){
     heading=(uint8_t)((ray+4)%8);enter(RETURN_HUB,now);
     // The confirmed line crossing is the stop point: don't coast through it
     // while the normal motor PWM ramp winds down.
     left=right=0;
    }else if(e>maxMs)fail(TURN_TIMEOUT,now);
    else drive(-turn,turn);
    break;
   }
   case RETURN_HUB:{
    bool candidate=e>=cruiseMs(z(Z_RETURN_MIN_MS))&&(v(P_HUB_MODE)==0?s.hub[hub]:e>=cruiseMs(z(Z_RETURN_ENTRY_MS)));
    if(hubTimer.test(candidate,now,v(P_HUB_CONFIRM_MS))){expectedHub=hub;enter(HUB_CENTRE,now);}
    else if(e>cruiseMs(z(Z_RETURN_MAX_MS)))fail(HUB_TIMEOUT,now);else if(candidate)drive(v(P_CENTRE_PWM),v(P_CENTRE_PWM));else follow(s,cruise,now);break;
   }
   case HUB_CENTRE:
    if(e>=centreMs(v(expectedHub?P_CENTRE_RIGHT_MS:P_CENTRE_LEFT_MS))){if(expectedHub==hub&&purpose==SEARCH_LEG&&!loaded)searchPos++;hub=expectedHub;plan(now);}else drive(v(P_CENTRE_PWM),v(P_CENTRE_PWM));break;
   case BRIDGE:{
    const bool marker=crossbar(s,now);
    if(clearTimer.test(!marker,now,v(P_MARKER_CLEAR_MS)))wideArmed=true;
    if(wideArmed&&wideTimer.test(marker,now,v(P_MARKER_MS))){wideArmed=false;if(crosses)crosses--;}
    bool candidate=e>=cruiseMs(v(P_BRIDGE_MIN_MS))&&crosses==0&&(v(P_HUB_MODE)==0?s.hub[1-hub]:e>=cruiseMs(v(P_BRIDGE_ENTRY_MS)));
    if(hubTimer.test(candidate,now,v(P_HUB_CONFIRM_MS))){expectedHub=1-hub;enter(HUB_CENTRE,now);}
    else if(e>cruiseMs(v(P_BRIDGE_MAX_MS)))fail(HUB_TIMEOUT,now);else if(candidate)drive(v(P_CENTRE_PWM),v(P_CENTRE_PWM));else follow(s,cruise,now);break;
   }
   case DELIVERY_CREEP:
    if(e>=slowMs(z(Z_DROP_ADVANCE_MS))){servoGoal=(uint8_t)v(P_LIFT_LOW);enter(LOWER,now);}else drive(slow,slow);break;
   case DROP_BACK:
    if(e>=slowMs(z(Z_DROP_BACK_MS))){if(s.contact)fail(CARGO_STUCK,now);else enter(DONE,now);}else drive(-slow,-slow);break;
   default:fail(BAD_SETTINGS,now);break;
  }
  services(now);
 }
};
