#pragma once
#include <Arduino.h>

// RB/Keyes L298P shield: the active buzzer is wired to D4 (HIGH = sound).
// No tone(), delay(), timers or interrupts: D10/D11 PWM and SG90 timing stay intact.
struct ShieldBuzzer {
 enum Event : uint8_t { READY, ARMED, START, STEP, MARKER, PICKED, DELIVERY, RELEASE,
                        COMPLETE, WARNING, STOPPED, ERROR, ACK, TEST, MODE_LINE, MODE_FULL };
 static const uint8_t PIN = 4;
 bool enabled = true;
 bool sounding = false;
 uint8_t remaining = 0, priority = 0;
 uint16_t onMs = 0, gapMs = 0;
 uint32_t changedAt = 0;

 void begin(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
 void silence(){
  digitalWrite(PIN,LOW);
  sounding = false; remaining = priority = 0;
 }
 void setEnabled(bool on){ enabled = on; if(!on)silence(); }
 bool busy() const { return remaining != 0; }

 void play(Event event,uint32_t now){
  uint8_t p = 1, count = 1; uint16_t on = 80, gap = 80;
  switch(event){
   case READY: on=90; break;
   case ARMED: count=2;on=65;gap=90;break;
   case START: p=2;on=230;break;
   case STEP: on=45;break;
   case MARKER: p=2;count=2;on=65;gap=85;break;
   case PICKED: p=2;count=2;on=155;gap=110;break;
   case DELIVERY: p=2;count=2;on=110;gap=90;break;
   case RELEASE: p=2;on=230;break;
   case COMPLETE: p=3;count=3;on=145;gap=95;break;
   case WARNING: p=3;count=2;on=85;gap=230;break;
   case STOPPED: p=4;count=2;on=250;gap=110;break;
   case ERROR: p=5;count=3;on=330;gap=140;break;
   case ACK: on=90;break;
   case TEST: count=3;on=75;gap=90;break;
   case MODE_LINE: count=3;on=100;gap=100;break;
   case MODE_FULL: on=400;break;
  }
  if(!enabled || (remaining && p<priority))return;
  priority=p;remaining=count;onMs=on;gapMs=gap;
  sounding=true;changedAt=now;digitalWrite(PIN,HIGH);
 }
 void tick(uint32_t now){
  if(!remaining || (uint32_t)(now-changedAt)<(sounding?onMs:gapMs))return;
  changedAt=now;
  if(sounding){
   sounding=false;digitalWrite(PIN,LOW);
   if(--remaining==0)priority=0;
  }else{
   sounding=true;digitalWrite(PIN,HIGH);
  }
 }
};
