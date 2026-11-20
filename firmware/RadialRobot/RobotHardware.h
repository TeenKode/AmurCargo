#pragma once
#include <Arduino.h>
#include "AmurServo.h"
#include <EEPROM.h>
#include <string.h>
#include <stdlib.h>
#include "RobotConfig.h"
#include "RadialCore.h"

#pragma pack(push,1)
struct StoredCalibration {uint32_t magic;uint8_t version,pins[3],mask;uint16_t white[3],black[3],hub[2][3],crc;};
struct StoredServoLimits { uint32_t magic; uint8_t low, high, reverse, check; };
struct StoredServoDirection {uint32_t magic;uint8_t reverse,check;};
struct StoredContactMode {uint32_t magic;uint8_t activeLow,pullup,check;};
// Dedicated 20-byte motor calibration record at EEPROM 960..979.
struct StoredMotorTuning {uint32_t magic;uint8_t minLeft,minRight;uint16_t leftTrim,rightTrim;uint8_t drive,loaded,approach,centre,turn,turnLoaded,rampStep,rampMs;uint16_t check;};
// Separate 10-byte optional record, 980..989: never overwrite servo EEPROM at 990.
struct StoredMotorDynamics {uint16_t magic;uint8_t kickPwm,kickMs,crawlLimit,crawlPwm,crawlPeriod,crawlMinOn;uint16_t check;};
#pragma pack(pop)
static_assert(sizeof(StoredMotorTuning)==20,"Unexpected EEPROM motor layout");
static_assert(sizeof(StoredMotorDynamics)==10,"Unexpected EEPROM dynamics layout");
inline uint16_t calibrationCrc(const StoredCalibration &c){const uint8_t *p=(const uint8_t*)&c;uint16_t crc=0xA51D;for(uint8_t i=0;i<sizeof(c)-2;i++){crc^=(uint16_t)p[i]<<8;for(uint8_t b=0;b<8;b++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}return crc;}
inline uint16_t normalizeAdc(uint16_t raw,uint16_t white,uint16_t black){int32_t span=(int32_t)black-white;if(!span)return 0;return (uint16_t)clamp16(((int32_t)raw-white)*1000L/span,0,1000);}

struct RobotHardware {
 Settings settings;RadialRobot robot;AmurServo lift;StoredCalibration cal;
 uint16_t raw[3],lineHistory[3][3];SensorInput input;
 uint8_t lineHistorySlot;bool lineHistoryReady;
 int16_t appliedLeft,appliedRight;
 uint8_t motorMinLeft,motorMinRight;
 uint8_t motorKickPwm,motorKickMs,motorCrawlLimit,motorCrawlPwm,motorCrawlPeriod,motorCrawlMinOn;
 int8_t lastRequestedSign[2];uint32_t kickStarted[2];
 bool armed,stream,calibrating,jogging,rawButton,stableButton,skipButtonRelease,lineOverflow,servoReversed,manualServoPending,contactPullup;
 uint8_t calKind,samples,lineLength;
 uint32_t sampleSum[3],lastRead,buttonChanged,buttonPressed,lastStream,jogStarted;
 uint8_t defaultServoLow,defaultServoHigh;
 uint16_t jogDuration;int16_t jogLeft,jogRight;int configError;char command[80];
 uint16_t v(Param p)const{return settings.v[p];}
 bool contact()const{return digitalRead(v(P_CONTACT_PIN))==(v(P_CONTACT_LOW)?LOW:HIGH);}
  void configureContactInput(){pinMode(v(P_CONTACT_PIN),contactPullup?INPUT_PULLUP:INPUT);}
  static uint8_t contactModeCheck(uint8_t activeLow,uint8_t pullup){return (uint8_t)(0xC7^activeLow^(pullup*0x5B));}
  void saveContactMode(){
   const uint8_t activeLow=(uint8_t)v(P_CONTACT_LOW),pullup=(uint8_t)contactPullup;
   const StoredContactMode mode={0x434F4E31UL,activeLow,pullup,contactModeCheck(activeLow,pullup)};
   EEPROM.put(1006,mode); // Servo limits at 990; direction at 1000..1005.
  }

 static uint16_t motorChecksum(const StoredMotorTuning &t){
  const uint8_t *p=(const uint8_t*)&t;uint16_t crc=0xA51D;
  for(uint8_t i=0;i<sizeof(t)-2;i++){crc^=(uint16_t)p[i]<<8;for(uint8_t j=0;j<8;j++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}
  return crc;
 }
 static bool validMotor(const StoredMotorTuning &t){
  return t.magic==0x4D4F5431UL&&t.check==motorChecksum(t)&&
   t.leftTrim>=500&&t.leftTrim<=1500&&t.rightTrim>=500&&t.rightTrim<=1500&&
   t.drive>=20&&t.drive<=220&&t.loaded>=20&&t.loaded<=220&&
   t.approach>=15&&t.approach<=180&&t.centre>=15&&t.centre<=180&&
   t.turn>=20&&t.turn<=200&&t.turnLoaded>=20&&t.turnLoaded<=200&&
   t.rampStep>=1&&t.rampMs>=1&&t.rampMs<=100;
 }
 StoredMotorTuning motorPreset()const{
  StoredMotorTuning t={0x4D4F5431UL,motorMinLeft,motorMinRight,v(P_LEFT_TRIM),v(P_RIGHT_TRIM),
   (uint8_t)v(P_DRIVE_PWM),(uint8_t)v(P_LOADED_PWM),(uint8_t)v(P_APPROACH_PWM),
   (uint8_t)v(P_CENTRE_PWM),(uint8_t)v(P_TURN_PWM),(uint8_t)v(P_TURN_LOADED_PWM),
   (uint8_t)v(P_RAMP_STEP),(uint8_t)v(P_RAMP_MS),0};
  t.check=motorChecksum(t);return t;
 }
 void applyMotor(const StoredMotorTuning &t){
  motorMinLeft=t.minLeft;motorMinRight=t.minRight;
  settings.v[P_LEFT_TRIM]=t.leftTrim;settings.v[P_RIGHT_TRIM]=t.rightTrim;
  settings.v[P_DRIVE_PWM]=t.drive;settings.v[P_LOADED_PWM]=t.loaded;
  settings.v[P_APPROACH_PWM]=t.approach;settings.v[P_CENTRE_PWM]=t.centre;
  settings.v[P_TURN_PWM]=t.turn;settings.v[P_TURN_LOADED_PWM]=t.turnLoaded;
  settings.v[P_RAMP_STEP]=t.rampStep;settings.v[P_RAMP_MS]=t.rampMs;
 }
 static uint16_t dynamicsChecksum(const StoredMotorDynamics &t){
  const uint8_t *p=(const uint8_t*)&t;uint16_t crc=0xB19D;
  for(uint8_t i=0;i<sizeof(t)-2;i++){crc^=(uint16_t)p[i]<<8;for(uint8_t j=0;j<8;j++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}
  return crc;
 }
 static bool validDynamics(const StoredMotorDynamics &t){
  return t.magic==0x4B53&&t.check==dynamicsChecksum(t)&&
   t.kickMs<=150&&t.crawlLimit<=150&&
   t.crawlPwm>=40&&t.crawlPeriod>=60&&t.crawlMinOn>=5&&
   t.crawlMinOn<t.crawlPeriod;
 }
 StoredMotorDynamics dynamicsPreset()const{
  StoredMotorDynamics t={0x4B53,motorKickPwm,motorKickMs,motorCrawlLimit,
   motorCrawlPwm,motorCrawlPeriod,motorCrawlMinOn,0};
  t.check=dynamicsChecksum(t);return t;
 }
 void applyDynamics(const StoredMotorDynamics &t){
  motorKickPwm=t.kickPwm;motorKickMs=t.kickMs;motorCrawlLimit=t.crawlLimit;
  motorCrawlPwm=t.crawlPwm;motorCrawlPeriod=t.crawlPeriod;motorCrawlMinOn=t.crawlMinOn;
  lastRequestedSign[0]=lastRequestedSign[1]=0;
 }
 // These effects never modify USB jog, which must remain an exact PWM measurement.
 // Kick only at a true stop->move transition; crawl uses aligned low-frequency
 // bursts so both wheels keep a common time base (no additional blocking delays).
 int16_t shapedMotor(int16_t requested,uint16_t trim,uint8_t minimum,uint8_t channel,uint32_t now){
  const int8_t sign=requested>0?1:requested<0?-1:0;
  const int8_t before=lastRequestedSign[channel];
  lastRequestedSign[channel]=sign;
  if(!sign)return 0;
  const uint16_t power=(uint16_t)clamp16((int32_t)abs16(requested)*trim/1000L,0,255);
  if(!before)kickStarted[channel]=now;
  else if(before!=sign)kickStarted[channel]=now-(uint32_t)motorKickMs; // never kick on reversal
  if(motorKickPwm&&motorKickMs&&(uint32_t)(now-kickStarted[channel])<motorKickMs &&
     power<motorKickPwm)return sign*(int16_t)motorKickPwm;
  if(motorCrawlLimit&&power<motorCrawlLimit){
   uint16_t on=(uint32_t)power*motorCrawlPeriod/motorCrawlPwm;
   if(on<motorCrawlMinOn)on=motorCrawlMinOn;
   if(on>=motorCrawlPeriod)on=motorCrawlPeriod-1;
   const uint8_t level=(now%motorCrawlPeriod)<on?motorCrawlPwm:0;
   return sign*(int16_t)level;
  }
  const int16_t steady=(int16_t)(power<minimum?minimum:power);
  return sign*steady;
 }
 // True stop remains zero; calibrated minimum is applied AFTER trim.
 static int16_t motorOutput(int16_t command,uint16_t trim,uint8_t minimum){
  if(!command)return 0;
  int16_t power=clamp16((int32_t)abs16(command)*trim/1000L,0,255);
  if(power<minimum)power=minimum;
  return command<0?-power:power;
 }
 enum CalibrationState { CAL_READY, CAL_INCOMPLETE, CAL_HUB_OVERLAP };
 CalibrationState calibrationState()const{
  const bool useHubSamples=v(P_HUB_MODE)==0;
  const uint8_t required=useHubSamples?15:3;
  if((cal.mask&required)!=required)return CAL_INCOMPLETE;
  for(uint8_t i=0;i<3;i++){
   if(cal.white[i]>1023||cal.black[i]>1023||abs16((int16_t)cal.black[i]-(int16_t)cal.white[i])<70)return CAL_INCOMPLETE;
  }
  if(!useHubSamples)return CAL_READY;
  // Disjoint tolerance ranges on any sensor make the two matches mutually exclusive.
  for(uint8_t i=0;i<3;i++){
   const int16_t left=normalizeAdc(cal.hub[0][i],cal.white[i],cal.black[i]);
   const int16_t right=normalizeAdc(cal.hub[1][i],cal.white[i],cal.black[i]);
   if(abs16(left-right)>2*v(P_HUB_TOLERANCE))return CAL_READY;
  }
  return CAL_HUB_OVERLAP;
 }
 bool calibrationReady()const{return calibrationState()==CAL_READY;}
 bool requireCalibration()const{
  const CalibrationState state=calibrationState();
  if(state==CAL_HUB_OVERLAP)Serial.println(F("CAL HUB OVERLAP: resample left and right circles."));
  else if(state==CAL_INCOMPLETE)Serial.println(F("CAL REQUIRED: sample white, black and required circles."));
  return state==CAL_READY;
 }
 void safeChannel(uint8_t a,uint8_t b,uint8_t en,int16_t value){
  analogWrite(en,0);digitalWrite(a,value>0?HIGH:LOW);digitalWrite(b,value<0?HIGH:LOW);analogWrite(en,abs16(value));
 }
 void dualPwm(uint8_t a,uint8_t b,int16_t value){if(value>=0){analogWrite(b,0);analogWrite(a,value);}else{analogWrite(a,0);analogWrite(b,-value);}}
 void shieldMotor(uint8_t direction,uint8_t speed,int16_t value,int16_t previous){
  if(value==previous)return; // No PWM teardown during steady-state tracking.
  // Disable PWM before real direction changes, not for speed-only updates.
  if(value!=0&&(previous==0||((value<0)!=(previous<0)))){
   analogWrite(speed,0);
   digitalWrite(direction,value>=0?HIGH:LOW);
  }
  analogWrite(speed,abs16(value));
 }
 void outputMotors(int16_t l,int16_t r,bool directPwm=false){
  if(configError)return;
  // USB jog remains an exact command, never shaped by kick or crawl.
  if(directPwm){lastRequestedSign[0]=lastRequestedSign[1]=0;l=clamp16(l,-255,255);r=clamp16(r,-255,255);}
  else{const uint32_t now=millis();l=shapedMotor(l,v(P_LEFT_TRIM),motorMinLeft,0,now);r=shapedMotor(r,v(P_RIGHT_TRIM),motorMinRight,1,now);}
  if(v(P_LEFT_REVERSE))l=-l;if(v(P_RIGHT_REVERSE))r=-r;
  if(v(P_DRIVER_MODE)==2){shieldMotor(v(P_LEFT_IN1),v(P_LEFT_EN),l,appliedLeft);shieldMotor(v(P_RIGHT_IN1),v(P_RIGHT_EN),r,appliedRight);}
  else if(v(P_DRIVER_MODE)==0){safeChannel(v(P_LEFT_IN1),v(P_LEFT_IN2),v(P_LEFT_EN),l);safeChannel(v(P_RIGHT_IN1),v(P_RIGHT_IN2),v(P_RIGHT_EN),r);}
  else{dualPwm(v(P_LEFT_IN1),v(P_LEFT_IN2),l);dualPwm(v(P_RIGHT_IN1),v(P_RIGHT_IN2),r);}
  if(v(P_STANDBY_PIN)!=255)digitalWrite(v(P_STANDBY_PIN),(l||r)?HIGH:LOW);
  appliedLeft=l;appliedRight=r;
 }
 void init(){
  Serial.begin(115200);loadUserSettings(settings);
  configError=settingsError(settings);if(!configError)configError=pinSettingsError(settings);
  armed=stream=calibrating=jogging=skipButtonRelease=lineOverflow=manualServoPending=false;lineLength=samples=0;lastRead=lastStream=buttonChanged=millis();
  lineHistorySlot=0;lineHistoryReady=false;appliedLeft=appliedRight=0;
  lastRequestedSign[0]=lastRequestedSign[1]=0;kickStarted[0]=kickStarted[1]=0;
  if(configError){Serial.print(F("CONFIG ERROR "));Serial.println(configError);return;}
  motorMinLeft=motorMinRight=70; // Starting estimate, not a measured motor threshold.
  StoredMotorTuning motorData;EEPROM.get(960,motorData);
  if(validMotor(motorData))applyMotor(motorData);
  // Conservative defaults: both dynamic modes are OPT-IN.
  motorKickPwm=0;motorKickMs=0;motorCrawlLimit=0;
  motorCrawlPwm=110;motorCrawlPeriod=160;motorCrawlMinOn=16;
  StoredMotorDynamics extra;EEPROM.get(980,extra);
  if(validDynamics(extra))applyDynamics(extra);
  // Shield uses only four motor pins. D4 is an active buzzer on the shield.
  if(v(P_DRIVER_MODE)==2){const uint8_t pins[4]={12,13,10,11};for(uint8_t i=0;i<4;i++){pinMode(pins[i],OUTPUT);digitalWrite(pins[i],LOW);}pinMode(4,OUTPUT);digitalWrite(4,LOW);}
  else{uint8_t outs[8]={(uint8_t)v(P_LEFT_IN1),(uint8_t)v(P_LEFT_IN2),(uint8_t)v(P_RIGHT_IN1),(uint8_t)v(P_RIGHT_IN2),(uint8_t)v(P_LEFT_EN),(uint8_t)v(P_RIGHT_EN),(uint8_t)v(P_LED_PIN),(uint8_t)v(P_STANDBY_PIN)};
  for(uint8_t i=0;i<8;i++)if(outs[i]!=255&&(v(P_DRIVER_MODE)==0||i<4||i>5)){pinMode(outs[i],OUTPUT);digitalWrite(outs[i],LOW);}}
  // START is a normally-open switch to GND. HW-511 is a powered comparator
   // module, not a switch: leave its signal unbiased unless explicitly requested.
   pinMode(v(P_START_PIN),INPUT_PULLUP);
   contactPullup=false;
   StoredContactMode contactMode;EEPROM.get(1006,contactMode);
   if(contactMode.magic==0x434F4E31UL&&contactMode.activeLow<=1&&contactMode.pullup<=1&&
      contactMode.check==contactModeCheck(contactMode.activeLow,contactMode.pullup)){
    settings.v[P_CONTACT_LOW]=contactMode.activeLow;contactPullup=contactMode.pullup;
   }
   configureContactInput();outputMotors(0,0);
  rawButton=stableButton=digitalRead(v(P_START_PIN))==LOW;buttonPressed=millis();
  EEPROM.get(0,cal);bool valid=cal.magic==0x52414431UL&&cal.version==1&&cal.crc==calibrationCrc(cal);
  StoredServoDirection direction;EEPROM.get(1000,direction);servoReversed=direction.magic==0x53525631UL&&direction.reverse<=1&&direction.check==(uint8_t)(direction.reverse^255)&&direction.reverse;
  defaultServoLow=v(P_LIFT_LOW);defaultServoHigh=v(P_LIFT_HIGH);
  StoredServoLimits limits;
  EEPROM.get(990, limits);
  if(limits.magic==0x534C4D31UL && limits.low<limits.high && limits.high<=180 &&
     limits.reverse==servoReversed && limits.check==servoLimitsCheck(limits)){
   settings.v[P_LIFT_LOW]=limits.low;
   settings.v[P_LIFT_HIGH]=limits.high;
  }
  robot.init(settings,millis());
  const uint8_t pins[3]={(uint8_t)v(P_LINE_LEFT),(uint8_t)v(P_LINE_CENTRE),(uint8_t)v(P_LINE_RIGHT)};
  for(uint8_t i=0;i<3;i++)if(cal.pins[i]!=pins[i])valid=false;
  if(!valid){memset(&cal,0,sizeof(cal));cal.magic=0x52414431UL;cal.version=1;for(uint8_t i=0;i<3;i++)cal.pins[i]=pins[i];}
  lift.attach(v(P_SERVO_PIN));lift.write(servoOutputAngle());
  memset(&input,0,sizeof(input));Serial.println(F("RADIAL READY. Hold START 2s to arm, release; short press to run. help"));
 }
 void readSensors(uint32_t now){
  if((uint32_t)(now-lastRead)<v(P_SENSOR_MS))return;lastRead=now;
  const uint8_t pins[3]={(uint8_t)v(P_LINE_LEFT),(uint8_t)v(P_LINE_CENTRE),(uint8_t)v(P_LINE_RIGHT)};
  for(uint8_t i=0;i<3;i++)raw[i]=analogRead(pins[i]);
  if(calibrating){for(uint8_t i=0;i<3;i++)sampleSum[i]+=raw[i];if(++samples>=32){
   for(uint8_t i=0;i<3;i++){uint16_t n=sampleSum[i]/32;if(calKind==0)cal.white[i]=n;else if(calKind==1)cal.black[i]=n;else cal.hub[calKind-2][i]=n;}
   cal.mask|=1U<<calKind;cal.crc=calibrationCrc(cal);calibrating=false;lineHistoryReady=false;Serial.println(F("CAL SAMPLE OK. save to EEPROM."));
  }}
  const bool basic=(cal.mask&3)==3;
  for(uint8_t i=0;i<3;i++){
   const uint16_t level=basic?normalizeAdc(raw[i],cal.white[i],cal.black[i]):0;
   if(!lineHistoryReady)for(uint8_t j=0;j<3;j++)lineHistory[i][j]=level;
   else lineHistory[i][lineHistorySlot]=level;
   const uint16_t a=lineHistory[i][0],b=lineHistory[i][1],c=lineHistory[i][2];
   // Reject single ADC spikes near black/white edges with a median of three.
   input.line[i]=(a>b)?(b>c?b:(a>c?c:a)):(a>c?a:(b>c?c:b));
  }
  lineHistoryReady=true;lineHistorySlot=(uint8_t)((lineHistorySlot+1)%3);
  for(uint8_t h=0;h<2;h++){input.hub[h]=basic&&(cal.mask&(1U<<(h+2)));for(uint8_t i=0;i<3;i++){uint16_t expected=normalizeAdc(cal.hub[h][i],cal.white[i],cal.black[i]);if(abs16((int16_t)input.line[i]-expected)>v(P_HUB_TOLERANCE))input.hub[h]=false;}}
 }
 void releaseButton(uint32_t held,uint32_t now){
  if(robot.active()||jogging||calibrating)return;
  if(robot.state==DONE){robot.init(settings,now);armed=false;Serial.println(F("RESET: reposition at configured hub and heading."));return;}
  if(robot.state==FAULT){if(held>=v(P_ARM_HOLD_MS)&&robot.servoAngle==v(P_LIFT_LOW)&&!contact()){robot.init(settings,now);armed=false;Serial.println(F("FAULT RESET"));}return;}
  if(held>=v(P_ARM_HOLD_MS)){armed=true;Serial.println(F("ARMED. Release, then short press START."));return;}
  if(!armed){Serial.println(F("NOT ARMED: hold START or send arm."));return;}
  if(!requireCalibration())return;
  if(robot.servoAngle!=v(P_LIFT_LOW)||robot.servoGoal!=v(P_LIFT_LOW)){Serial.println(F("LOWER FORKS BEFORE START"));return;}
  if(contact()){Serial.println(F("CONTACT ALREADY PRESSED"));return;}
  robot.start(now);
 }
 void button(uint32_t now){
  bool pressed=digitalRead(v(P_START_PIN))==LOW;
  if(pressed!=rawButton){
   rawButton=pressed;buttonChanged=now;
  }
  // Remember the stop even if the timed jog expires during button debounce.
  if(pressed&&jogging)skipButtonRelease=true;
  if((uint32_t)(now-buttonChanged)<35)return;
  if(pressed==stableButton){if(!pressed)skipButtonRelease=false;return;}
  stableButton=pressed;
  if(pressed){
   buttonPressed=now;
   if(robot.active()){robot.fail(ABORTED,now);armed=false;}
   if(skipButtonRelease){jogging=false;armed=false;robot.stop();outputMotors(0,0);}
  }else if(!skipButtonRelease){
   releaseButton(now-buttonPressed,now);
  }
 }
 void status(){
  Serial.print(F("state="));Serial.print((int)robot.state);Serial.print(F(" fault="));Serial.print((int)robot.fault);Serial.print(F(" armed="));Serial.print(armed);
  Serial.print(F(" hub="));Serial.print(robot.hub);Serial.print(F(" ray="));Serial.print(robot.ray);Serial.print(F(" held="));Serial.print(robot.loaded);Serial.print(F(" angle="));Serial.print(robot.servoAngle);
  Serial.print(F(" servo_reverse="));Serial.print(servoReversed?1:0);Serial.print(F(" servo_output="));Serial.print(servoOutputAngle());
  Serial.print(F(" servo_goal="));Serial.print(robot.servoGoal);
  Serial.print(F(" servo_low="));Serial.print(v(P_LIFT_LOW));
  Serial.print(F(" servo_high="));Serial.print(v(P_LIFT_HIGH));
  Serial.print(F(" servo_settled="));Serial.print(servoSettled(millis())?1:0);
  Serial.print(F(" start_button="));Serial.print(stableButton?1:0);
   Serial.print(F(" start_raw="));Serial.print(digitalRead(v(P_START_PIN)));
   Serial.print(F(" start_pin="));Serial.print(v(P_START_PIN));
   Serial.print(F(" start_hold_ms="));Serial.print(stableButton?(uint32_t)(millis()-buttonPressed):0UL);
  Serial.print(F(" raw="));for(uint8_t i=0;i<3;i++){Serial.print(raw[i]);Serial.print(' ');}Serial.print(F(" line="));for(uint8_t i=0;i<3;i++){Serial.print(input.line[i]);Serial.print(' ');}
  Serial.print(F(" contact="));Serial.print(contact());
   Serial.print(F(" contact_raw="));Serial.print(digitalRead(v(P_CONTACT_PIN)));
   Serial.print(F(" contact_low="));Serial.print(v(P_CONTACT_LOW));
   Serial.print(F(" contact_pullup="));Serial.print(contactPullup?1:0);
   Serial.print(F(" contact_pin="));Serial.print(v(P_CONTACT_PIN));
  // Diagnostic values make illumination problems and failed ray acquisition
  // distinguishable from a motor or PID tuning problem in a saved serial log.
  Serial.print(F(" pwm="));Serial.print(robot.left);Serial.print(' ');Serial.print(robot.right);
  Serial.print(F(" target="));Serial.print(robot.wantLeft);Serial.print(' ');Serial.print(robot.wantRight);
  Serial.print(F(" err="));Serial.print(robot.previousError);
  Serial.print(F(" corr="));Serial.print(robot.correction);
  Serial.print(F(" dfilter="));Serial.print(robot.filteredDerivative);
  Serial.print(F(" lost_ms="));Serial.print(robot.lostTimer.active?(uint32_t)(millis()-robot.lostTimer.since):0UL);
  Serial.print(F(" marker="));Serial.print(robot.markerCandidateNow?1:0);
  Serial.print(F(" marker_base="));Serial.print(robot.markerBaseLeft);Serial.print(' ');Serial.print(robot.markerBaseRight);
  Serial.print(F(" marker_rise="));Serial.print(robot.markerRiseLeft);Serial.print(' ');Serial.print(robot.markerRiseRight);
  Serial.print(F(" marker_confirm_ms="));Serial.print(robot.wideTimer.active?(uint32_t)(millis()-robot.wideTimer.since):0UL);
  Serial.print(F(" cal="));Serial.print((int)calibrationState());
  Serial.print(F(" motor_min="));Serial.print(motorMinLeft);Serial.print(',');Serial.print(motorMinRight);
  Serial.print(F(" motor_trim="));Serial.print(v(P_LEFT_TRIM));Serial.print(',');Serial.print(v(P_RIGHT_TRIM));
  Serial.print(F(" motor_speed="));Serial.print(v(P_DRIVE_PWM));Serial.print(',');Serial.print(v(P_LOADED_PWM));Serial.print(',');
  Serial.print(v(P_APPROACH_PWM));Serial.print(',');Serial.print(v(P_CENTRE_PWM));Serial.print(',');
  Serial.print(v(P_TURN_PWM));Serial.print(',');Serial.print(v(P_TURN_LOADED_PWM));
  Serial.print(F(" motor_ramp="));Serial.print(v(P_RAMP_STEP));Serial.print(',');Serial.print(v(P_RAMP_MS));
  Serial.print(F(" motor_dynamics="));Serial.print(motorKickPwm);Serial.print(',');
  Serial.print(motorKickMs);Serial.print(',');Serial.print(motorCrawlLimit);Serial.print(',');
  Serial.print(motorCrawlPwm);Serial.print(',');Serial.print(motorCrawlPeriod);Serial.print(',');
  Serial.print(motorCrawlMinOn);
  Serial.print(F(" motor_applied="));Serial.print(appliedLeft);Serial.print(',');Serial.print(appliedRight);
  Serial.print(F(" motor_jog="));Serial.println(jogging?1:0);
 }
 static uint8_t servoLimitsCheck(const StoredServoLimits &limits){
  return 0xA7 ^ limits.low ^ (uint8_t)(limits.high*3) ^ limits.reverse;
 }
 uint8_t servoOutputAngle()const{return servoReversed?180-robot.servoAngle:robot.servoAngle;}
 // This is commanded-position dwell, not feedback from the physical SG90 shaft.
 bool servoSettled(uint32_t now)const{
  return robot.servoAngle==robot.servoGoal &&
         (uint32_t)(now-robot.lastServo)>=v(P_SERVO_SETTLE_MS);
 }
 bool number(char *s,long &n){if(!s)return false;char *end;n=strtol(s,&end,10);return *s&&!*end;}
 void handle(char *line,uint32_t now){
  char *cmd=strtok(line," \t");if(!cmd)return;
  if(!strcmp(cmd,"stop")){manualServoPending=false;jogging=false;robot.fail(ABORTED,now);armed=false;outputMotors(0,0);Serial.println(F("STOPPED. Servo holds current angle."));return;}
  if(!strcmp(cmd,"status")){status();return;}
  if(!strcmp(cmd,"stream")){
   char *mode=strtok(0," \t");
   if(!mode)stream=!stream;
   else if(!strcmp(mode,"on"))stream=true;
   else if(!strcmp(mode,"off"))stream=false;
   else {Serial.println(F("Use stream on or off."));return;}
   if(stream)status();
   return;
  }
  if(robot.active()||jogging){Serial.println(F("BUSY: only status, stream, stop."));return;}
   // Recover a sensor even in FAULT when a wrong contact level blocks RESET.
   if(!strcmp(cmd,"contact")){
    char *mode=strtok(0," \t"),*value=strtok(0," \t");
    if(!mode || (value && strtok(0," \t")) || calibrating){
     Serial.println(F("Use contact high|low or contact pullup on|off while stopped."));return;
    }
    if(!value && !strcmp(mode,"high"))settings.v[P_CONTACT_LOW]=0;
    else if(!value && !strcmp(mode,"low"))settings.v[P_CONTACT_LOW]=1;
    else if(value && !strcmp(mode,"pullup") && (!strcmp(value,"on")||!strcmp(value,"off"))){
     contactPullup=!strcmp(value,"on");configureContactInput();
    }else{Serial.println(F("Use contact high|low or contact pullup on|off."));return;}
    armed=false;robot.contactTimer.clear();robot.heldTimer.clear();
    saveContactMode();Serial.println(F("CONTACT CONFIG SAVED"));status();return;
   }
  if(!strcmp(cmd,"help")){Serial.println(F("cal white|black|left|right; save; arm; low; high; angle N; limits LOW HIGH; servo normal|reverse detached; contact high|low; contact pullup on|off; motor set [12 values]|dynamics KICK PWMMS CRAWL_LIMIT CRAWL_PWM PERIOD MINON|save|clear; jog L R ms (-255..255); status; stream; reset; erase; stop"));return;}
  if(!strcmp(cmd,"low")||!strcmp(cmd,"high")){robot.servoGoal=!strcmp(cmd,"low")?v(P_LIFT_LOW):v(P_LIFT_HIGH);manualServoPending=true;Serial.println(F("MANUAL SERVO: support any load."));status();return;}
  if(!strcmp(cmd,"reset")){if(robot.servoAngle!=v(P_LIFT_LOW)||contact()){Serial.println(F("RESET REFUSED: lower forks and remove load."));return;}robot.init(settings,now);manualServoPending=false;armed=false;return;}
  if(robot.state!=IDLE){Serial.println(F("RESET REQUIRED"));return;}

  if(!strcmp(cmd,"motor")){
   char *action=strtok(0," \t");
   if(action&&!strcmp(action,"dynamics")){
    long a[6];bool ok=true;
    for(uint8_t i=0;i<6;i++){char *word=strtok(0," \t");if(!number(word,a[i])||a[i]<0||a[i]>255){ok=false;break;}}
    if(strtok(0," \t"))ok=false;
    if(!ok){Serial.println(F("MOTOR REFUSED: dynamics needs 6 integers 0..255"));return;}
    StoredMotorDynamics t={0x4B53,(uint8_t)a[0],(uint8_t)a[1],(uint8_t)a[2],
     (uint8_t)a[3],(uint8_t)a[4],(uint8_t)a[5],0};
    t.check=dynamicsChecksum(t);
    if(!validDynamics(t)){Serial.println(F("MOTOR REFUSED: invalid kick/crawl settings"));return;}
    applyDynamics(t);armed=false;
    Serial.println(F("MOTOR DYNAMICS UPDATED: RAM only; use motor save"));status();return;
   }
   if(action&&!strcmp(action,"set")){
    long a[12];bool ok=true;
    for(uint8_t i=0;i<12;i++){
     char *word=strtok(0," \t");
     if(!number(word,a[i])){ok=false;break;}
     if(i!=2&&i!=3&&(a[i]<0||a[i]>255))ok=false;
    }
    if(strtok(0," \t"))ok=false;
    if(!ok||a[2]<500||a[2]>1500||a[3]<500||a[3]>1500){Serial.println(F("MOTOR REFUSED: invalid arguments"));return;}
    StoredMotorTuning t=motorPreset();
    t.minLeft=(uint8_t)a[0];t.minRight=(uint8_t)a[1];t.leftTrim=(uint16_t)a[2];t.rightTrim=(uint16_t)a[3];
    t.drive=(uint8_t)a[4];t.loaded=(uint8_t)a[5];t.approach=(uint8_t)a[6];t.centre=(uint8_t)a[7];
    t.turn=(uint8_t)a[8];t.turnLoaded=(uint8_t)a[9];t.rampStep=(uint8_t)a[10];t.rampMs=(uint8_t)a[11];
    t.check=motorChecksum(t);
    if(!validMotor(t)){Serial.println(F("MOTOR REFUSED: values out of range"));return;}
    applyMotor(t);armed=false;Serial.println(F("MOTOR UPDATED: RAM only; use motor save"));status();return;
   }
   if(action&&!strcmp(action,"save")&&!strtok(0," \t")){
    const StoredMotorTuning t=motorPreset();EEPROM.put(960,t);
    const StoredMotorDynamics extra=dynamicsPreset();EEPROM.put(980,extra);
    Serial.println(F("MOTOR SAVED: EEPROM"));status();return;
   }
   if(action&&!strcmp(action,"clear")&&!strtok(0," \t")){
    const uint32_t blank=0;EEPROM.put(960,blank);EEPROM.put(980,blank);armed=false;
    Serial.println(F("MOTOR CLEARED: reboot to restore firmware values"));return;
   }
   Serial.println(F("MOTOR REFUSED: use motor set, motor dynamics [6 values], motor save or motor clear"));return;
  }
  if(!strcmp(cmd,"angle")||!strcmp(cmd,"limits")){
   if(calibrating||contact()){
    Serial.println(F("SERVO REFUSED: finish sensor calibration and remove load"));return;
   }
   long low,high;
   char *first=strtok(0," \t"),*second=strtok(0," \t");
   if(!number(first,low)||low<0||low>180||strtok(0," \t")){
    Serial.println(F("SERVO REFUSED: angle must be 0..180"));return;
   }
   if(!strcmp(cmd,"angle")){
    if(second){Serial.println(F("Use angle N"));return;}
    armed=false;
    robot.servoGoal=(uint8_t)low;
    manualServoPending=true;
   }else{
    if(!number(second,high)||high<=low||high>180||!servoSettled(now)){
     Serial.println(F("SERVO REFUSED: wait for servo and set low < high <= 180"));return;
    }
    StoredServoLimits limits={0x534C4D31UL,(uint8_t)low,(uint8_t)high,(uint8_t)servoReversed,0};
    limits.check=servoLimitsCheck(limits);
    EEPROM.put(990,limits);
    settings.v[P_LIFT_LOW]=limits.low;
    settings.v[P_LIFT_HIGH]=limits.high;
    armed=false;
    Serial.println(F("SERVO LIMITS SAVED"));
   }
   status();
   return;
  }
  if(!strcmp(cmd,"servo")){
   char *mode=strtok(0," \t"),*detached=strtok(0," \t");
   if(!mode||!detached||strcmp(detached,"detached")||strtok(0," \t")||(strcmp(mode,"normal")&&strcmp(mode,"reverse"))||calibrating||contact()||robot.servoAngle!=v(P_LIFT_LOW)||robot.servoGoal!=v(P_LIFT_LOW)){Serial.println(F("SERVO REFUSED: idle, low, no load; detach horn; servo normal|reverse detached"));return;}
   const bool reverse=!strcmp(mode,"reverse");
   if(reverse!=servoReversed){
    EEPROM.put(990,(uint8_t)0);
    settings.v[P_LIFT_LOW]=defaultServoLow;
    settings.v[P_LIFT_HIGH]=defaultServoHigh;
    robot.servoAngle=robot.servoGoal=v(P_LIFT_LOW);
   }
   manualServoPending=false;servoReversed=reverse;StoredServoDirection direction={0x53525631UL,(uint8_t)servoReversed,(uint8_t)(servoReversed^255)};EEPROM.put(1000,direction);armed=false;lift.write(servoOutputAngle());Serial.print(F("SERVO SAVED reverse="));Serial.println(servoReversed?1:0);return;
  }
  if(!strcmp(cmd,"arm")){armed=true;Serial.println(F("ARMED"));return;}
  if(!strcmp(cmd,"erase")){memset(&cal,0,sizeof(cal));cal.magic=0x52414431UL;cal.version=1;cal.pins[0]=v(P_LINE_LEFT);cal.pins[1]=v(P_LINE_CENTRE);cal.pins[2]=v(P_LINE_RIGHT);cal.crc=calibrationCrc(cal);EEPROM.put(0,cal);armed=false;Serial.println(F("CAL ERASED. Servo direction retained."));return;}
  if(!strcmp(cmd,"save")){if(!requireCalibration())return;cal.crc=calibrationCrc(cal);EEPROM.put(0,cal);Serial.println(F("EEPROM SAVED"));return;}
  if(!strcmp(cmd,"cal")){
   char *kind=strtok(0," \t");int8_t k=kind&& !strcmp(kind,"white")?0:kind&&!strcmp(kind,"black")?1:kind&&!strcmp(kind,"left")?2:kind&&!strcmp(kind,"right")?3:-1;
   if(k<0||calibrating){Serial.println(F("CAL ARGUMENT ERROR"));return;}calKind=k;samples=0;for(uint8_t i=0;i<3;i++)sampleSum[i]=0;calibrating=true;armed=false;return;
  }
  if(!strcmp(cmd,"jog")){
   long l,r,t;char *a=strtok(0," \t"),*b=strtok(0," \t"),*c=strtok(0," \t");
   if(!armed||calibrating||digitalRead(v(P_START_PIN))==LOW||robot.servoAngle!=v(P_LIFT_LOW)||robot.servoGoal!=v(P_LIFT_LOW)||contact()||!number(a,l)||!number(b,r)||!number(c,t)||strtok(0," \t")||l<-255||l>255||r<-255||r>255||t<1||t>2000||(!l&&!r)){Serial.println(F("JOG REFUSED: arm, low, no load; nonzero PWM +/-255, 1..2000ms."));return;}
   jogLeft=l;jogRight=r;jogDuration=t;jogStarted=now;jogging=true;
   Serial.print(F("JOG START left="));Serial.print(jogLeft);
   Serial.print(F(" right="));Serial.print(jogRight);
   Serial.print(F(" duration_ms="));Serial.println(jogDuration);
   return;
  }
  Serial.println(F("UNKNOWN COMMAND"));
 }
 void serial(uint32_t now){
  while(Serial.available()){
   char c=Serial.read();if(c=='\r')continue;
   if(c=='\n'){if(!lineOverflow){command[lineLength]=0;handle(command,now);}else Serial.println(F("COMMAND TOO LONG"));lineLength=0;lineOverflow=false;}
   else if(lineLength<sizeof(command)-1)command[lineLength++]=c;else lineOverflow=true;
  }
 }
 void tick(){
  uint32_t now=millis();if(configError)return;
  serial(now);readSensors(now);button(now);input.contact=contact();input.abort=false;
  const RobotState before=robot.state;
  if(jogging){if((uint32_t)(now-jogStarted)>=jogDuration){jogging=false;robot.stop();Serial.println(F("JOG DONE"));}else robot.drive(jogLeft,jogRight);robot.services(now);}else robot.tick(input,now);
  // Clear, timestampable serial diagnostics when a loading/drop-off stripe is
  // actually accepted, rather than merely showing a brief black ADC reading.
  if(before==SEARCH_OUT&&robot.state==APPROACH)Serial.println(F("MARKER CONFIRMED: LOADING ZONE"));
  else if(before==DELIVERY_OUT&&robot.state==DELIVERY_CREEP)Serial.println(F("MARKER CONFIRMED: DELIVERY ZONE"));
  // Apply the requested test PWM immediately; ramp() is for the mission only.
  // The next tick returns to zero as soon as the jog deadline expires.
  outputMotors(jogging?jogLeft:robot.left,jogging?jogRight:robot.right,jogging);
  lift.write(servoOutputAngle());
  // For USB angle tuning, publish an arrival status even with stream off.
  // Otherwise the browser only sees the old angle sent before movement,
  // and "capture current" never knows that SG90 has reached the target.
  if(manualServoPending&&servoSettled(now)){
    manualServoPending=false;status();
  }
  if(v(P_LED_PIN)!=255)digitalWrite(v(P_LED_PIN),robot.state==FAULT?((now/150)%2):robot.state==DONE?HIGH:armed?((now/700)%2):LOW);
  if(stream&&(uint32_t)(now-lastStream)>=150){lastStream=now;status();}
 }
};
