#pragma once
#include <cstring>
struct EEPROMMock {
 unsigned char bytes[1024]={};
 template<class T>void get(int offset,T &v){std::memcpy(&v,bytes+offset,sizeof(v));}
 template<class T>void put(int offset,const T &v){std::memcpy(bytes+offset,&v,sizeof(v));}
};
inline EEPROMMock EEPROM;
