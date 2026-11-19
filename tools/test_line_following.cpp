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
 std::puts("PASS: tracking, adaptive speed, derivative filter, reacquisition and bounded line recovery");
}
