#pragma once
#include "Settings.h"
// Values below are initial tuning values, not measurements of the physical robot.
inline void loadDefaultSettings(Settings &s){
 s.v[P_START_HUB]=0;
 s.v[P_START_HEADING]=0;
 s.v[P_DROP_RAY]=0;
 s.v[P_HUB_MODE]=0;
 s.v[P_BRIDGE_CROSSES]=1;
 s.v[P_DRIVER_MODE]=2;
 s.v[P_LEFT_IN1]=12;
 s.v[P_LEFT_IN2]=255;
 s.v[P_LEFT_EN]=10;
 s.v[P_RIGHT_IN1]=13;
 s.v[P_RIGHT_IN2]=255;
 s.v[P_RIGHT_EN]=11;
 s.v[P_STANDBY_PIN]=255;
 s.v[P_SERVO_PIN]=9;
 s.v[P_START_PIN]=17;
 s.v[P_CONTACT_PIN]=2;
 s.v[P_LINE_LEFT]=14;
 s.v[P_LINE_CENTRE]=15;
 s.v[P_LINE_RIGHT]=16;
 s.v[P_LED_PIN]=255;
 s.v[P_LEFT_REVERSE]=0;
 s.v[P_RIGHT_REVERSE]=0;
 s.v[P_CONTACT_LOW]=0;
 s.v[P_DRIVE_PWM]=85;
 s.v[P_LOADED_PWM]=75;
 s.v[P_APPROACH_PWM]=55;
 s.v[P_CENTRE_PWM]=80;
 s.v[P_TURN_PWM]=85;
 s.v[P_TURN_LOADED_PWM]=75;
 s.v[P_LEFT_TRIM]=1000;
 s.v[P_RIGHT_TRIM]=1000;
 s.v[P_RAMP_STEP]=5;
 s.v[P_RAMP_MS]=10;
 s.v[P_LINE_THRESHOLD]=350;
 s.v[P_WIDE_THRESHOLD]=800;
 s.v[P_HUB_TOLERANCE]=85;
 s.v[P_KP]=60;
 s.v[P_KD]=25;
 s.v[P_MAX_CORRECTION]=28;
 s.v[P_SENSOR_MS]=10;
 s.v[P_LOST_MS]=250;
 s.v[P_MARKER_MS]=35;
 s.v[P_MARKER_CLEAR_MS]=80;
 s.v[P_HUB_CONFIRM_MS]=60;
 s.v[P_CONTACT_MS]=30;
 s.v[P_TURN45_MS]=510;
 s.v[P_TURN45_LOADED_MS]=579;
 s.v[P_TURN_START_MS]=55;
 s.v[P_TURN_RIGHT_SCALE]=1000;
 s.v[P_UTURN_MIN_MS]=500;
 s.v[P_UTURN_MAX_MS]=2800;
 s.v[P_UTURN_LOADED_MIN_MS]=600;
 s.v[P_UTURN_LOADED_MAX_MS]=3300;
 s.v[P_TURN_LINE_MS]=30;
 s.v[P_SETTLE_MS]=120;
 s.v[P_HUB_EXIT_MS]=650;
 s.v[P_ACQUIRE_MS]=1800;
 s.v[P_CENTRE_LEFT_MS]=1650;
 s.v[P_CENTRE_RIGHT_MS]=1650;
 s.v[P_BRIDGE_MIN_MS]=2000;
 s.v[P_BRIDGE_MAX_MS]=15000;
 s.v[P_BRIDGE_ENTRY_MS]=9000;
 s.v[P_REVERSE_RATIO]=1000;
 s.v[P_MISSION_SECONDS]=240;
 s.v[P_LIFT_LOW]=20;
 s.v[P_LIFT_HIGH]=140;
 s.v[P_SERVO_STEP]=1;
 s.v[P_SERVO_MS]=15;
 s.v[P_SERVO_SETTLE_MS]=350;
 s.v[P_CHECK_HELD_CONTACT]=0;
 s.v[P_HELD_LOST_MS]=300;
 s.v[P_ARM_HOLD_MS]=2000;
 for(uint8_t h=0;h<2;h++)for(uint8_t r=0;r<8;r++){
 s.zone[h][r][Z_OUT_MIN_MS]=500;
 s.zone[h][r][Z_OUT_MAX_MS]=7500;
 s.zone[h][r][Z_SEARCH_MS]=850;
 s.zone[h][r][Z_BACKOFF_MS]=800;
 s.zone[h][r][Z_RETURN_MIN_MS]=350;
 s.zone[h][r][Z_RETURN_MAX_MS]=7500;
 s.zone[h][r][Z_RETURN_ENTRY_MS]=1800;
 s.zone[h][r][Z_DROP_ADVANCE_MS]=0;
 s.zone[h][r][Z_DROP_BACK_MS]=1300;
 }
 s.searchCount=7;for(uint8_t i=0;i<7;i++)s.search[i]=i+1;
}

// WEB_FLASH_CONFIG: fixed-size flash configuration patched by the offline page.
#ifdef ARDUINO_ARCH_AVR
#include <avr/pgmspace.h>
static_assert(sizeof(Settings)==440,"Web flash configuration layout changed");
const uint8_t firmwareConfig[] PROGMEM __attribute__((used))={65,77,85,82,67,70,71,50,48,50,54,86,48,48,49,33,0,0,0,0,0,0,0,0,1,0,2,0,12,0,255,0,10,0,13,0,255,0,11,0,255,0,9,0,17,0,2,0,14,0,15,0,16,0,255,0,0,0,0,0,0,0,85,0,75,0,55,0,80,0,85,0,75,0,232,3,232,3,5,0,10,0,94,1,32,3,85,0,60,0,25,0,28,0,10,0,250,0,35,0,80,0,60,0,30,0,254,1,67,2,55,0,232,3,244,1,240,10,88,2,228,12,30,0,120,0,138,2,8,7,114,6,114,6,208,7,152,58,40,35,232,3,240,0,20,0,140,0,1,0,15,0,94,1,0,0,44,1,208,7,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,244,1,76,29,82,3,32,3,94,1,76,29,8,7,0,0,20,5,1,2,3,4,5,6,7,7,228,123};
inline void loadUserSettings(Settings &s){
 memcpy_P(&s,firmwareConfig+16,sizeof(s));uint16_t crc=65535;const uint8_t *p=(const uint8_t*)&s;
 for(uint16_t i=0;i<sizeof(s);i++){crc^=(uint16_t)p[i]<<8;for(uint8_t j=0;j<8;j++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;}
 if(crc!=pgm_read_word(firmwareConfig+16+sizeof(s)))s.v[0]=65535;
}
#else
inline void loadUserSettings(Settings &s){loadDefaultSettings(s);}
#endif
