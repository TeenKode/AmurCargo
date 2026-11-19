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
#pragma pack(pop)
inline uint16_t calibrationCrc(const StoredCalibration &c){const uint8_t *p=(const uint8_t*)&c;uint16_t crc=0xA51D;for(uint8_t i=0;i<sizeof(c)-2;i++){crc^=(uint16_t)p[i]<<8;for(uint8_t b=0;b<8;b++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}return crc;}
inline uint16_t normalizeAdc(uint16_t raw,uint16_t white,uint16_t black){int32_t span=(int32_t)black-white;if(!span)return 0;return (uint16_t)clamp16(((int32_t)raw-white)*1000L/span,0,1000);}

struct RobotHardware {
 Settings settings;RadialRobot robot;AmurServo lift;StoredCalibration cal;
 uint16_t raw[3];SensorInput input;
 bool armed,stream,calibrating,jogging,rawButton,stableButton,skipButtonRelease,lineOverflow,servoReversed,manualServoPending;
 uint8_t calKind,samples,lineLength;
 uint32_t sampleSum[3],lastRead,buttonChanged,buttonPressed,lastStream,jogStarted;
 uint8_t defaultServoLow,defaultServoHigh;
 uint16_t jogDuration;int16_t jogLeft,jogRight;int configError;char command[80];
 uint16_t v(Param p)const{return settings.v[p];}
 bool contact()const{return digitalRead(v(P_CONTACT_PIN))==(v(P_CONTACT_LOW)?LOW:HIGH);}
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
 void shieldMotor(uint8_t direction,uint8_t speed,int16_t value){
  // Disable the H-bridge before a direction change; do not brake a powered motor.
  analogWrite(speed,0);
  digitalWrite(direction,value>=0?HIGH:LOW);
  analogWrite(speed,abs16(value));
 }
 void outputMotors(int16_t l,int16_t r){
  if(configError)return;
  l=clamp16((int32_t)l*v(P_LEFT_TRIM)/1000L,-255,255);r=clamp16((int32_t)r*v(P_RIGHT_TRIM)/1000L,-255,255);
  if(v(P_LEFT_REVERSE))l=-l;if(v(P_RIGHT_REVERSE))r=-r;
  if(v(P_DRIVER_MODE)==2){shieldMotor(v(P_LEFT_IN1),v(P_LEFT_EN),l);shieldMotor(v(P_RIGHT_IN1),v(P_RIGHT_EN),r);}
  else if(v(P_DRIVER_MODE)==0){safeChannel(v(P_LEFT_IN1),v(P_LEFT_IN2),v(P_LEFT_EN),l);safeChannel(v(P_RIGHT_IN1),v(P_RIGHT_IN2),v(P_RIGHT_EN),r);}
  else{dualPwm(v(P_LEFT_IN1),v(P_LEFT_IN2),l);dualPwm(v(P_RIGHT_IN1),v(P_RIGHT_IN2),r);}
  if(v(P_STANDBY_PIN)!=255)digitalWrite(v(P_STANDBY_PIN),(l||r)?HIGH:LOW);
 }
 void init(){
  Serial.begin(115200);loadUserSettings(settings);
  configError=settingsError(settings);if(!configError)configError=pinSettingsError(settings);
  armed=stream=calibrating=jogging=skipButtonRelease=lineOverflow=manualServoPending=false;lineLength=samples=0;lastRead=lastStream=buttonChanged=millis();
  if(configError){Serial.print(F("CONFIG ERROR "));Serial.println(configError);return;}
  // Shield uses only four motor pins. D4 is an active buzzer on the shield.
  if(v(P_DRIVER_MODE)==2){const uint8_t pins[4]={12,13,10,11};for(uint8_t i=0;i<4;i++){pinMode(pins[i],OUTPUT);digitalWrite(pins[i],LOW);}pinMode(4,OUTPUT);digitalWrite(4,LOW);}
  else{uint8_t outs[8]={(uint8_t)v(P_LEFT_IN1),(uint8_t)v(P_LEFT_IN2),(uint8_t)v(P_RIGHT_IN1),(uint8_t)v(P_RIGHT_IN2),(uint8_t)v(P_LEFT_EN),(uint8_t)v(P_RIGHT_EN),(uint8_t)v(P_LED_PIN),(uint8_t)v(P_STANDBY_PIN)};
  for(uint8_t i=0;i<8;i++)if(outs[i]!=255&&(v(P_DRIVER_MODE)==0||i<4||i>5)){pinMode(outs[i],OUTPUT);digitalWrite(outs[i],LOW);}}
  pinMode(v(P_START_PIN),INPUT_PULLUP);pinMode(v(P_CONTACT_PIN),INPUT_PULLUP);outputMotors(0,0);
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
   cal.mask|=1U<<calKind;cal.crc=calibrationCrc(cal);calibrating=false;Serial.println(F("CAL SAMPLE OK. save to EEPROM."));
  }}
  bool basic=(cal.mask&3)==3;for(uint8_t i=0;i<3;i++)input.line[i]=basic?normalizeAdc(raw[i],cal.white[i],cal.black[i]):0;
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
  Serial.print(F(" start_button="));Serial.print(stableButton?1:0);
  Serial.print(F(" raw="));for(uint8_t i=0;i<3;i++){Serial.print(raw[i]);Serial.print(' ');}Serial.print(F(" line="));for(uint8_t i=0;i<3;i++){Serial.print(input.line[i]);Serial.print(' ');}
  Serial.print(F(" contact="));Serial.print(contact());
  // Diagnostic values make illumination problems and failed ray acquisition
  // distinguishable from a motor or PID tuning problem in a saved serial log.
  Serial.print(F(" pwm="));Serial.print(robot.left);Serial.print(' ');Serial.print(robot.right);
  Serial.print(F(" target="));Serial.print(robot.wantLeft);Serial.print(' ');Serial.print(robot.wantRight);
  Serial.print(F(" err="));Serial.print(robot.previousError);
  Serial.print(F(" corr="));Serial.print(robot.correction);
  Serial.print(F(" dfilter="));Serial.print(robot.filteredDerivative);
  Serial.print(F(" lost_ms="));Serial.print(robot.lostTimer.active?(uint32_t)(millis()-robot.lostTimer.since):0UL);
  Serial.print(F(" cal="));Serial.println((int)calibrationState());
 }
 static uint8_t servoLimitsCheck(const StoredServoLimits &limits){
  return 0xA7 ^ limits.low ^ (uint8_t)(limits.high*3) ^ limits.reverse;
 }
 uint8_t servoOutputAngle()const{return servoReversed?180-robot.servoAngle:robot.servoAngle;}
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
  if(!strcmp(cmd,"help")){Serial.println(F("cal white|black|left|right; save; arm; low; high; angle N; limits LOW HIGH; servo normal|reverse detached; jog L R ms; status; stream; reset; erase; stop"));return;}
  if(!strcmp(cmd,"low")||!strcmp(cmd,"high")){robot.servoGoal=!strcmp(cmd,"low")?v(P_LIFT_LOW):v(P_LIFT_HIGH);manualServoPending=true;Serial.println(F("MANUAL SERVO: support any load."));status();return;}
  if(!strcmp(cmd,"reset")){if(robot.servoAngle!=v(P_LIFT_LOW)||contact()){Serial.println(F("RESET REFUSED: lower forks and remove load."));return;}robot.init(settings,now);manualServoPending=false;armed=false;return;}
  if(robot.state!=IDLE){Serial.println(F("RESET REQUIRED"));return;}
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
    if(!number(second,high)||high<=low||high>180||robot.servoAngle!=robot.servoGoal){
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
   if(!armed||calibrating||digitalRead(v(P_START_PIN))==LOW||robot.servoAngle!=v(P_LIFT_LOW)||robot.servoGoal!=v(P_LIFT_LOW)||contact()||!number(a,l)||!number(b,r)||!number(c,t)||strtok(0," \t")||l<-150||l>150||r<-150||r>150||t<1||t>2000){Serial.println(F("JOG REFUSED: arm, low, no load; PWM +/-150, 1..2000ms."));return;}
   jogLeft=l;jogRight=r;jogDuration=t;jogStarted=now;jogging=true;return;
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
  if(jogging){if((uint32_t)(now-jogStarted)>=jogDuration){jogging=false;robot.stop();}else robot.drive(jogLeft,jogRight);robot.services(now);}else robot.tick(input,now);
  outputMotors(robot.left,robot.right);lift.write(servoOutputAngle());
  // For USB angle tuning, publish an arrival status even with stream off.
  // Otherwise the browser only sees the old angle sent before movement,
  // and "capture current" never knows that SG90 has reached the target.
  if(manualServoPending&&robot.servoAngle==robot.servoGoal){
    manualServoPending=false;status();
  }
  if(v(P_LED_PIN)!=255)digitalWrite(v(P_LED_PIN),robot.state==FAULT?((now/150)%2):robot.state==DONE?HIGH:armed?((now/700)%2):LOW);
  if(stream&&(uint32_t)(now-lastStream)>=150){lastStream=now;status();}
 }
};
