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
  // Compare B interrupt is pre-armed in the cycle before the rising edge.
  // Previous-cycle matches must not accidentally shorten the pulse.
  assert(!amurServoShouldEndPulse(false,edge.cycle,edge.cycle));
  for(int phase=0;phase<edge.cycle;phase++)
   assert(!amurServoShouldEndPulse(true,(uint8_t)phase,edge.cycle));
  assert(amurServoShouldEndPulse(true,edge.cycle,edge.cycle));
 }
 puts("PASS: 181 servo angles, pre-armed compare-B guard and correct falling edge");
}
