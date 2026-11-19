#include "AmurServo.h"
#include <cassert>
#include <cstdio>
int main(){
 assert(amurServoAngleUs(0)==544&&amurServoAngleUs(180)==2400);
 int previous=0;
 constexpr int frameUs=256*4*20;
 assert(frameUs==20480); // 20 Timer0 cycles, 16 MHz / 64.
 for(int angle=0;angle<=180;angle++){
  const int requested=amurServoAngleUs(angle);
  assert(requested>=544&&requested<=2400);
  if(angle)assert(requested>previous);
  previous=requested;
  const int reverse=amurServoAngleUs(180-angle);
  assert(requested+reverse>=2943&&requested+reverse<=2944);
  AmurServoEdge edge=amurServoFallingEdge(requested);
  assert(edge.cycle<=2&&edge.compare>4);
  int generated=((int(edge.cycle)*256+edge.compare)-4)*4;
  assert(generated-requested>=-16 && generated-requested<=16);
  assert(generated>0&&generated<frameUs);
  // Compare B interrupt is pre-armed in the cycle before the rising edge.
  // Previous-cycle matches must not accidentally shorten the pulse.
  assert(!amurServoShouldEndPulse(false,edge.cycle,edge.cycle));
  for(int phase=0;phase<edge.cycle;phase++)
   assert(!amurServoShouldEndPulse(true,(uint8_t)phase,edge.cycle));
  assert(amurServoShouldEndPulse(true,edge.cycle,edge.cycle));
 }
 assert(amurServoAngleUs(-10)==544&&amurServoAngleUs(200)==2400);
 puts("PASS: 181 monotonic servo angles, reverse mapping, bounded timer quantization and stable 20.48ms frame");
}
