#pragma once
class Servo {
 bool on=false;
 public:
 int position=0;
 void write(int a){position=a;}
 void attach(int){on=true;}
 bool attached(){return on;}
};
