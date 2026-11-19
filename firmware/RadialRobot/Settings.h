#pragma once
#include <stdint.h>
enum Param {
 P_START_HUB=0,
 P_START_HEADING=1,
 P_DROP_RAY=2,
 P_HUB_MODE=3,
 P_BRIDGE_CROSSES=4,
 P_DRIVER_MODE=5,
 P_LEFT_IN1=6,
 P_LEFT_IN2=7,
 P_LEFT_EN=8,
 P_RIGHT_IN1=9,
 P_RIGHT_IN2=10,
 P_RIGHT_EN=11,
 P_STANDBY_PIN=12,
 P_SERVO_PIN=13,
 P_START_PIN=14,
 P_CONTACT_PIN=15,
 P_LINE_LEFT=16,
 P_LINE_CENTRE=17,
 P_LINE_RIGHT=18,
 P_LED_PIN=19,
 P_LEFT_REVERSE=20,
 P_RIGHT_REVERSE=21,
 P_CONTACT_LOW=22,
 P_DRIVE_PWM=23,
 P_LOADED_PWM=24,
 P_APPROACH_PWM=25,
 P_CENTRE_PWM=26,
 P_TURN_PWM=27,
 P_TURN_LOADED_PWM=28,
 P_LEFT_TRIM=29,
 P_RIGHT_TRIM=30,
 P_RAMP_STEP=31,
 P_RAMP_MS=32,
 P_LINE_THRESHOLD=33,
 P_WIDE_THRESHOLD=34,
 P_HUB_TOLERANCE=35,
 P_KP=36,
 P_KD=37,
 P_MAX_CORRECTION=38,
 P_SENSOR_MS=39,
 P_LOST_MS=40,
 P_MARKER_MS=41,
 P_MARKER_CLEAR_MS=42,
 P_HUB_CONFIRM_MS=43,
 P_CONTACT_MS=44,
 P_TURN45_MS=45,
 P_TURN45_LOADED_MS=46,
 P_TURN_START_MS=47,
 P_TURN_RIGHT_SCALE=48,
 P_UTURN_MIN_MS=49,
 P_UTURN_MAX_MS=50,
 P_UTURN_LOADED_MIN_MS=51,
 P_UTURN_LOADED_MAX_MS=52,
 P_TURN_LINE_MS=53,
 P_SETTLE_MS=54,
 P_HUB_EXIT_MS=55,
 P_ACQUIRE_MS=56,
 P_CENTRE_LEFT_MS=57,
 P_CENTRE_RIGHT_MS=58,
 P_BRIDGE_MIN_MS=59,
 P_BRIDGE_MAX_MS=60,
 P_BRIDGE_ENTRY_MS=61,
 P_REVERSE_RATIO=62,
 P_MISSION_SECONDS=63,
 P_LIFT_LOW=64,
 P_LIFT_HIGH=65,
 P_SERVO_STEP=66,
 P_SERVO_MS=67,
 P_SERVO_SETTLE_MS=68,
 P_CHECK_HELD_CONTACT=69,
 P_HELD_LOST_MS=70,
 P_ARM_HOLD_MS=71,
 P_COUNT};
enum ZoneParam {
 Z_OUT_MIN_MS=0,
 Z_OUT_MAX_MS=1,
 Z_SEARCH_MS=2,
 Z_BACKOFF_MS=3,
 Z_RETURN_MIN_MS=4,
 Z_RETURN_MAX_MS=5,
 Z_RETURN_ENTRY_MS=6,
 Z_DROP_ADVANCE_MS=7,
 Z_DROP_BACK_MS=8,
 Z_COUNT};
struct Settings { uint16_t v[P_COUNT]; uint16_t zone[2][8][Z_COUNT]; uint8_t search[7]; uint8_t searchCount; };
inline uint8_t bridgeRay(uint8_t hub){return hub?4:0;}
inline int settingsError(const Settings &s){
 if(s.v[0]<0 || s.v[0]>1)return 1;
 if(s.v[1]<0 || s.v[1]>7)return 2;
 if(s.v[2]<0 || s.v[2]>7)return 3;
 if(s.v[3]<0 || s.v[3]>1)return 4;
 if(s.v[4]<0 || s.v[4]>4)return 5;
 if(s.v[5]<2 || s.v[5]>2)return 6;
 if(s.v[6]<2 || s.v[6]>19)return 7;
 if(s.v[7]<2 || s.v[7]>255)return 8;
 if(s.v[8]<2 || s.v[8]>255)return 9;
 if(s.v[9]<2 || s.v[9]>19)return 10;
 if(s.v[10]<2 || s.v[10]>255)return 11;
 if(s.v[11]<2 || s.v[11]>255)return 12;
 if(s.v[12]<2 || s.v[12]>255)return 13;
 if(s.v[13]<2 || s.v[13]>19)return 14;
 if(s.v[14]<2 || s.v[14]>19)return 15;
 if(s.v[15]<2 || s.v[15]>19)return 16;
 if(s.v[16]<14 || s.v[16]>19)return 17;
 if(s.v[17]<14 || s.v[17]>19)return 18;
 if(s.v[18]<14 || s.v[18]>19)return 19;
 if(s.v[19]<2 || s.v[19]>255)return 20;
 if(s.v[20]<0 || s.v[20]>1)return 21;
 if(s.v[21]<0 || s.v[21]>1)return 22;
 if(s.v[22]<0 || s.v[22]>1)return 23;
 if(s.v[23]<20 || s.v[23]>220)return 24;
 if(s.v[24]<20 || s.v[24]>220)return 25;
 if(s.v[25]<15 || s.v[25]>180)return 26;
 if(s.v[26]<15 || s.v[26]>180)return 27;
 if(s.v[27]<20 || s.v[27]>200)return 28;
 if(s.v[28]<20 || s.v[28]>200)return 29;
 if(s.v[29]<500 || s.v[29]>1500)return 30;
 if(s.v[30]<500 || s.v[30]>1500)return 31;
 if(s.v[31]<1 || s.v[31]>255)return 32;
 if(s.v[32]<1 || s.v[32]>100)return 33;
 if(s.v[33]<50 || s.v[33]>950)return 34;
 if(s.v[34]<400 || s.v[34]>1000)return 35;
 if(s.v[35]<5 || s.v[35]>250)return 36;
 if(s.v[36]<0 || s.v[36]>500)return 37;
 if(s.v[37]<0 || s.v[37]>500)return 38;
 if(s.v[38]<0 || s.v[38]>180)return 39;
 if(s.v[39]<2 || s.v[39]>100)return 40;
 if(s.v[40]<30 || s.v[40]>2000)return 41;
 if(s.v[41]<5 || s.v[41]>300)return 42;
 if(s.v[42]<10 || s.v[42]>500)return 43;
 if(s.v[43]<10 || s.v[43]>500)return 44;
 if(s.v[44]<5 || s.v[44]>300)return 45;
 if(s.v[45]<50 || s.v[45]>3000)return 46;
 if(s.v[46]<50 || s.v[46]>3500)return 47;
 if(s.v[47]<0 || s.v[47]>1000)return 48;
 if(s.v[48]<500 || s.v[48]>1500)return 49;
 if(s.v[49]<100 || s.v[49]>10000)return 50;
 if(s.v[50]<200 || s.v[50]>15000)return 51;
 if(s.v[51]<100 || s.v[51]>12000)return 52;
 if(s.v[52]<200 || s.v[52]>15000)return 53;
 if(s.v[53]<5 || s.v[53]>200)return 54;
 if(s.v[54]<0 || s.v[54]>1000)return 55;
 if(s.v[55]<50 || s.v[55]>5000)return 56;
 if(s.v[56]<100 || s.v[56]>8000)return 57;
 if(s.v[57]<0 || s.v[57]>6000)return 58;
 if(s.v[58]<0 || s.v[58]>6000)return 59;
 if(s.v[59]<0 || s.v[59]>20000)return 60;
 if(s.v[60]<1000 || s.v[60]>60000)return 61;
 if(s.v[61]<1000 || s.v[61]>50000)return 62;
 if(s.v[62]<200 || s.v[62]>3000)return 63;
 if(s.v[63]<30 || s.v[63]>1800)return 64;
 if(s.v[64]<0 || s.v[64]>180)return 65;
 if(s.v[65]<0 || s.v[65]>180)return 66;
 if(s.v[66]<1 || s.v[66]>10)return 67;
 if(s.v[67]<5 || s.v[67]>100)return 68;
 if(s.v[68]<0 || s.v[68]>3000)return 69;
 if(s.v[69]<0 || s.v[69]>1)return 70;
 if(s.v[70]<20 || s.v[70]>2000)return 71;
 if(s.v[71]<500 || s.v[71]>5000)return 72;
 if(s.v[P_LINE_THRESHOLD]>=s.v[P_WIDE_THRESHOLD])return 200;
 if(s.v[P_UTURN_MIN_MS]>=s.v[P_UTURN_MAX_MS] || s.v[P_UTURN_LOADED_MIN_MS]>=s.v[P_UTURN_LOADED_MAX_MS])return 201;
 if(s.v[P_DROP_RAY]==bridgeRay(1-s.v[P_START_HUB]))return 202;
 if(s.searchCount<1 || s.searchCount>7)return 203;
 uint8_t seen=0; for(uint8_t i=0;i<s.searchCount;i++){uint8_t r=s.search[i];if(r>7 || r==bridgeRay(s.v[P_START_HUB]) || (seen&(1U<<r)))return 204;seen|=1U<<r;}
 for(uint8_t h=0;h<2;h++)for(uint8_t r=0;r<8;r++){
 if(s.zone[h][r][0]<0 || s.zone[h][r][0]>5000)return 210;
 if(s.zone[h][r][1]<500 || s.zone[h][r][1]>30000)return 211;
 if(s.zone[h][r][2]<0 || s.zone[h][r][2]>5000)return 212;
 if(s.zone[h][r][3]<0 || s.zone[h][r][3]>5000)return 213;
 if(s.zone[h][r][4]<0 || s.zone[h][r][4]>5000)return 214;
 if(s.zone[h][r][5]<500 || s.zone[h][r][5]>30000)return 215;
 if(s.zone[h][r][6]<0 || s.zone[h][r][6]>20000)return 216;
 if(s.zone[h][r][7]<0 || s.zone[h][r][7]>4000)return 217;
 if(s.zone[h][r][8]<100 || s.zone[h][r][8]>6000)return 218;
 if(s.zone[h][r][Z_OUT_MIN_MS]>=s.zone[h][r][Z_OUT_MAX_MS] || s.zone[h][r][Z_RETURN_MIN_MS]>=s.zone[h][r][Z_RETURN_MAX_MS])return 230;
 }
 if(s.v[P_LIFT_LOW]>=s.v[P_LIFT_HIGH])return 231;
 return 0; }
inline bool usableMotorPwm(uint16_t p){return p==3||p==5||p==6||p==11;}
inline int pinSettingsError(const Settings &s){
 uint8_t pins[16],n=0;
 // RB L298P: fixed DIR A=12 PWM A=10 DIR B=13 PWM B=11.
 // D13 is unavailable for the status LED; D9 reserved for SG90.
 if(s.v[P_DRIVER_MODE]!=2 || s.v[P_LEFT_IN1]!=12 || s.v[P_RIGHT_IN1]!=13 || s.v[P_LEFT_EN]!=10 || s.v[P_RIGHT_EN]!=11 || s.v[P_LEFT_IN2]!=255 || s.v[P_RIGHT_IN2]!=255 || s.v[P_SERVO_PIN]!=9 || s.v[P_LED_PIN]!=255)return 305;
 pins[n++]=12;pins[n++]=13;pins[n++]=10;pins[n++]=11;
 if(s.v[P_START_PIN]==4 || s.v[P_CONTACT_PIN]==4)return 306; // D4 active buzzer
 pins[n++]=s.v[P_SERVO_PIN];pins[n++]=s.v[P_START_PIN];pins[n++]=s.v[P_CONTACT_PIN];pins[n++]=s.v[P_LINE_LEFT];pins[n++]=s.v[P_LINE_CENTRE];pins[n++]=s.v[P_LINE_RIGHT];
 if(s.v[P_LED_PIN]!=255)pins[n++]=s.v[P_LED_PIN];if(s.v[P_STANDBY_PIN]!=255)pins[n++]=s.v[P_STANDBY_PIN];
 for(uint8_t i=0;i<n;i++){if(pins[i]<2||pins[i]>19)return 303;for(uint8_t j=0;j<i;j++)if(pins[i]==pins[j])return 304;}return 0;}
