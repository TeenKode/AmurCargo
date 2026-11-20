#pragma once
#include <stdint.h>
#ifdef __AVR__
#include <avr/pgmspace.h>
#endif
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
struct SettingRange { uint16_t min, max; };
static const SettingRange paramRanges[]
#ifdef __AVR__
 PROGMEM
#endif
 = {
 {0, 1}, // START_HUB
 {0, 7}, // START_HEADING
 {0, 7}, // DROP_RAY
 {0, 1}, // HUB_MODE
 {0, 4}, // BRIDGE_CROSSES
 {2, 2}, // DRIVER_MODE
 {2, 19}, // LEFT_IN1
 {2, 255}, // LEFT_IN2
 {2, 255}, // LEFT_EN
 {2, 19}, // RIGHT_IN1
 {2, 255}, // RIGHT_IN2
 {2, 255}, // RIGHT_EN
 {2, 255}, // STANDBY_PIN
 {2, 19}, // SERVO_PIN
 {2, 19}, // START_PIN
 {2, 19}, // CONTACT_PIN
 {14, 19}, // LINE_LEFT
 {14, 19}, // LINE_CENTRE
 {14, 19}, // LINE_RIGHT
 {2, 255}, // LED_PIN
 {0, 1}, // LEFT_REVERSE
 {0, 1}, // RIGHT_REVERSE
 {0, 1}, // CONTACT_LOW
 {20, 220}, // DRIVE_PWM
 {20, 220}, // LOADED_PWM
 {15, 180}, // APPROACH_PWM
 {15, 180}, // CENTRE_PWM
 {20, 200}, // TURN_PWM
 {20, 200}, // TURN_LOADED_PWM
 {500, 1500}, // LEFT_TRIM
 {500, 1500}, // RIGHT_TRIM
 {1, 255}, // RAMP_STEP
 {1, 100}, // RAMP_MS
 {50, 950}, // LINE_THRESHOLD
 {400, 1000}, // WIDE_THRESHOLD
 {5, 250}, // HUB_TOLERANCE
 {0, 500}, // KP
 {0, 500}, // KD
 {0, 180}, // MAX_CORRECTION
 {2, 100}, // SENSOR_MS
 {30, 2000}, // LOST_MS
 {5, 300}, // MARKER_MS
 {10, 500}, // MARKER_CLEAR_MS
 {10, 500}, // HUB_CONFIRM_MS
 {5, 300}, // CONTACT_MS
 {50, 3000}, // TURN45_MS
 {50, 3500}, // TURN45_LOADED_MS
 {0, 1000}, // TURN_START_MS
 {500, 1500}, // TURN_RIGHT_SCALE
 {100, 10000}, // UTURN_MIN_MS
 {200, 15000}, // UTURN_MAX_MS
 {100, 12000}, // UTURN_LOADED_MIN_MS
 {200, 15000}, // UTURN_LOADED_MAX_MS
 {5, 200}, // TURN_LINE_MS
 {0, 1000}, // SETTLE_MS
 {50, 5000}, // HUB_EXIT_MS
 {100, 8000}, // ACQUIRE_MS
 {0, 6000}, // CENTRE_LEFT_MS
 {0, 6000}, // CENTRE_RIGHT_MS
 {0, 20000}, // BRIDGE_MIN_MS
 {1000, 60000}, // BRIDGE_MAX_MS
 {1000, 50000}, // BRIDGE_ENTRY_MS
 {200, 3000}, // REVERSE_RATIO
 {30, 1800}, // MISSION_SECONDS
 {0, 180}, // LIFT_LOW
 {0, 180}, // LIFT_HIGH
 {1, 10}, // SERVO_STEP
 {5, 100}, // SERVO_MS
 {0, 3000}, // SERVO_SETTLE_MS
 {0, 1}, // CHECK_HELD_CONTACT
 {20, 2000}, // HELD_LOST_MS
 {500, 5000}, // ARM_HOLD_MS
};
static const SettingRange zoneRanges[]
#ifdef __AVR__
 PROGMEM
#endif
 = {
 {0, 5000}, // OUT_MIN_MS
 {500, 30000}, // OUT_MAX_MS
 {0, 5000}, // SEARCH_MS
 {0, 5000}, // BACKOFF_MS
 {0, 5000}, // RETURN_MIN_MS
 {500, 30000}, // RETURN_MAX_MS
 {0, 20000}, // RETURN_ENTRY_MS
 {0, 4000}, // DROP_ADVANCE_MS
 {100, 6000}, // DROP_BACK_MS
};
inline bool inSettingRange(uint16_t value,const SettingRange &range){
#ifdef __AVR__
 return value>=pgm_read_word(&range.min)&&value<=pgm_read_word(&range.max);
#else
 return value>=range.min&&value<=range.max;
#endif
}
inline int settingsError(const Settings &s){
 for(uint8_t i=0;i<P_COUNT;i++)if(!inSettingRange(s.v[i],paramRanges[i]))return i+1;
 if(s.v[P_LINE_THRESHOLD]>=s.v[P_WIDE_THRESHOLD])return 200;
 if(s.v[P_UTURN_MIN_MS]>=s.v[P_UTURN_MAX_MS] || s.v[P_UTURN_LOADED_MIN_MS]>=s.v[P_UTURN_LOADED_MAX_MS])return 201;
 if(s.v[P_DROP_RAY]==bridgeRay(1-s.v[P_START_HUB]))return 202;
 if(s.searchCount<1 || s.searchCount>7)return 203;
 uint8_t seen=0; for(uint8_t i=0;i<s.searchCount;i++){uint8_t r=s.search[i];if(r>7 || r==bridgeRay(s.v[P_START_HUB]) || (seen&(1U<<r)))return 204;seen|=1U<<r;}
 for(uint8_t h=0;h<2;h++)for(uint8_t r=0;r<8;r++){
 for(uint8_t i=0;i<Z_COUNT;i++)if(!inSettingRange(s.zone[h][r][i],zoneRanges[i]))return 210+i;
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
