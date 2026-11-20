#include "ShieldBuzzer.h"
#include <cassert>
#include <cstdio>

int main(){
 ShieldBuzzer b;
 b.begin();
 assert(pinModes[4]==OUTPUT && outputPins[4]==LOW && !b.busy());
 b.play(ShieldBuzzer::ARMED,clockMs);
 assert(b.busy() && outputPins[4]==HIGH);
 clockMs+=64;b.tick(clockMs);assert(outputPins[4]==HIGH);
 clockMs++;b.tick(clockMs);assert(outputPins[4]==LOW);
 clockMs+=90;b.tick(clockMs);assert(outputPins[4]==HIGH);
 clockMs+=65;b.tick(clockMs);assert(!b.busy() && outputPins[4]==LOW);
 // A lower-priority event must never hide an urgent fault.
 b.play(ShieldBuzzer::ERROR,clockMs);
 b.play(ShieldBuzzer::STEP,clockMs);
 assert(b.remaining==3 && b.priority==5);
 clockMs+=330;b.tick(clockMs);assert(outputPins[4]==LOW);
 clockMs+=140;b.tick(clockMs);assert(outputPins[4]==HIGH);
 b.play(ShieldBuzzer::STOPPED,clockMs);
 assert(b.priority==5);
 // The clock wraps without causing a stuck HIGH output.
 b.silence();
 clockMs=0xFFFFFFF0UL;
 b.play(ShieldBuzzer::READY,clockMs);
 clockMs+=90;b.tick(clockMs);assert(!b.busy() && outputPins[4]==LOW);
 b.play(ShieldBuzzer::ERROR,clockMs);
 b.setEnabled(false);
 assert(!b.busy() && outputPins[4]==LOW);
 b.play(ShieldBuzzer::TEST,clockMs);
 assert(!b.busy() && outputPins[4]==LOW);
 b.setEnabled(true);
 b.play(ShieldBuzzer::TEST,clockMs);
 assert(b.busy() && outputPins[4]==HIGH);
 b.silence();
 assert(!b.busy() && outputPins[4]==LOW);
 puts("PASS: L298P active buzzer patterns, priority, mute, non-blocking timing and rollover");
}
