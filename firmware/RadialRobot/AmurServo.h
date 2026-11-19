#pragma once
#include <stdint.h>
// AmurCargo UNO/Nano SG90 driver. Timer1 PWM on motor D10 stays operational.
// Timer0 still runs Arduino's original PWM mode/prescaler/overflow millis ISR.
// OCR0A/B and their compare interrupts are reserved: never PWM on D5/D6.
static inline uint16_t amurServoAngleUs(int angle){
 if(angle<0)angle=0;if(angle>180)angle=180;
 return (uint16_t)(544UL+(uint32_t)angle*1856UL/180UL);
}
struct AmurServoEdge {uint8_t cycle,compare;};
static inline AmurServoEdge amurServoFallingEdge(uint16_t pulseUs){
 // Timer0 Fast PWM at 16MHz / 64: tick=4us, overflow=1024us.
 // Servo pulse starts at Timer0 OCR0A=4 (16us into cycle).
 uint16_t ticks=(uint16_t)(4U+(pulseUs+2U)/4U);
 uint8_t cycle=(uint8_t)(ticks/256U),compare=(uint8_t)(ticks%256U);
 if(compare<=4){
  if(cycle>0&&compare<=2){--cycle;compare=255;}
  else compare=6;
 }
 return {cycle,compare};
}
#if defined(ARDUINO_ARCH_AVR) && defined(__AVR_ATmega328P__)
#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
namespace AmurServoTimer {
static volatile uint16_t pulseUs=1500;
static volatile uint8_t phase=0,fallCycle=1;
static volatile bool pulseHigh=false,connected=false;
}
ISR(TIMER0_COMPA_vect){
 using namespace AmurServoTimer;
 if(!connected)return;
 if(++phase>=20){
  phase=0; pulseHigh=true; PORTB|=_BV(PB1); // SG90 D9 signal HIGH
  if(fallCycle==0)TIMSK0|=_BV(OCIE0B);
  return;
 }
 if(phase==19){
  const AmurServoEdge e=amurServoFallingEdge(pulseUs);
  OCR0B=e.compare; // Fast PWM double-buffered; committed at Timer0 BOTTOM.
  fallCycle=e.cycle;
 }
 if(pulseHigh&&phase==fallCycle)TIMSK0|=_BV(OCIE0B);
}
ISR(TIMER0_COMPB_vect){
 using namespace AmurServoTimer;
 PORTB&=(uint8_t)~_BV(PB1);
 pulseHigh=false;
 TIMSK0&=(uint8_t)~_BV(OCIE0B);
}
class AmurServo {
public:
 void attach(uint8_t pin){
  if(pin!=9)return; // strict shield pinSettingsError() verifies D9
  pinMode(9,OUTPUT);digitalWrite(9,LOW);
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE){
   AmurServoTimer::connected=false;
   AmurServoTimer::phase=0;AmurServoTimer::pulseHigh=false;
   OCR0A=4;
   TIMSK0&=(uint8_t)~_BV(OCIE0B);
   TIMSK0|=_BV(OCIE0A);
   AmurServoTimer::connected=true;
  }
 }
 void write(int angle){
  const uint16_t us=amurServoAngleUs(angle);
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE){AmurServoTimer::pulseUs=us;}
 }
};
#else
#include <Servo.h> // Host test mock; not linked for AVR.
using AmurServo=Servo;
#endif
