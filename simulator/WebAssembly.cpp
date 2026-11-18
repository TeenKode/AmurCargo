#include "../firmware/RadialRobot/RobotConfig.h"
#include "../firmware/RadialRobot/RadialCore.h"
#include <stddef.h>
extern "C" void *memset(void *d,int v,size_t n){volatile unsigned char *p=(volatile unsigned char*)d;while(n--)*p++=(unsigned char)v;return d;}
extern "C" void *memcpy(void *d,const void *s,size_t n){unsigned char *p=(unsigned char*)d;const unsigned char *q=(const unsigned char*)s;while(n--)*p++=*q++;return d;}
static Settings settings;
static RadialRobot robot;
extern "C" {
void config_default(){loadUserSettings(settings);}
void config_set(int index,int value){if(index>=0&&index<P_COUNT)settings.v[index]=(uint16_t)value;}
int config_get(int index){return index>=0&&index<P_COUNT?settings.v[index]:0;}
void zone_set(int h,int r,int k,int value){if(h>=0&&h<2&&r>=0&&r<8&&k>=0&&k<Z_COUNT)settings.zone[h][r][k]=(uint16_t)value;}
void search_set(int pos,int ray){if(pos>=0&&pos<7)settings.search[pos]=(uint8_t)ray;}
void search_count(int count){settings.searchCount=(uint8_t)count;}
int config_error(){int e=settingsError(settings);return e?e:pinSettingsError(settings);}
void reset_robot(){robot.init(settings,0);}
int start_robot(int now){return robot.start((uint32_t)now);}
void robot_tick(int now,int l,int c,int r,int h0,int h1,int contact,int abort){SensorInput s={{(uint16_t)l,(uint16_t)c,(uint16_t)r},{h0!=0,h1!=0},contact!=0,abort!=0};robot.tick(s,(uint32_t)now);}
int get_left(){return robot.left;}int get_right(){return robot.right;}int get_servo(){return robot.servoAngle;}
int get_state(){return robot.state;}int get_fault(){return robot.fault;}int get_loaded(){return robot.loaded;}
int get_hub(){return robot.hub;}int get_ray(){return robot.ray;}int get_heading(){return robot.heading;}int get_search(){return robot.searchPos;}int get_crosses(){return robot.crosses;}
int settings_size(){return sizeof(Settings);}int engine_size(){return sizeof(RadialRobot);}
}
