#pragma once
#include <cstdint>
#include <algorithm>
#include <deque>
#include <cstring>
using std::min; using std::max; using std::abs;
using byte=uint8_t;
constexpr uint8_t A0=14,A1=15,A2=16,A3=17,A4=18,A5=19;
constexpr int LOW=0,HIGH=1,INPUT=0,OUTPUT=1,INPUT_PULLUP=2;
struct __FlashStringHelper {};
#define F(x) reinterpret_cast<const __FlashStringHelper*>(x)
inline unsigned long clockMs=0;
inline int inputPins[32],outputPins[32],adcPins[32],pinModes[32];
inline unsigned long millis(){return clockMs;}
inline void delay(unsigned long t){clockMs+=t;}
inline void pinMode(uint8_t p,int mode){pinModes[p]=mode;}
inline int digitalRead(uint8_t p){return inputPins[p];}
inline void digitalWrite(uint8_t p,int v){outputPins[p]=v;}
inline void analogWrite(uint8_t p,int v){outputPins[p]=v;}
inline int analogRead(uint8_t p){return adcPins[p];}
template<typename T>T constrain(T v,T a,T b){return std::max(a,std::min(v,b));}
struct SerialMock {
 std::deque<char> commands;
 void begin(int){}
 int available(){return (int)commands.size();}
 char read(){char c=commands.front();commands.pop_front();return c;}
 template<class T>void print(T){}
 template<class T>void println(T){}
 void println(){}
};
inline SerialMock Serial;
