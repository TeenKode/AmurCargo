#include "AmurServo.h"
#include <cassert>
#include <cstdio>
int main(){
 assert(amurServoAngleUs(0)==544&&amurServoAngleUs(180)==2400);
 for(int angle=0;angle<=180;angle++){
  const int requested=amurServoAngleUs(angle);
  AmurServoEdge edge=amurServoFallingEdge(requested);
  assert(edge.cycle<=2&&edge.compare>4);
  int generated=((int(edge.cycle)*256+edge.compare)-4)*4;
  assert(generated-requested>=-16 && generated-requested<=16);
 }
 puts("PASS: SG90 Timer0 compare scheduling over all angles");
}
