(function(global){'use strict';
const names=['Ожидание','Поворот в круге','Выезд из круга','Захват линии','Поиск: движение к зоне','Проверка погрузочной зоны','Подъём груза','Отход от зоны','Разворот на луче','Возврат в круг','Подъезд к центру','Переезд между кругами','Движение к разгрузке','Установка позиции разгрузки','Опускание груза','Выход из-под груза','Задание выполнено','Остановка по ошибке'];
const faults=['Нет ошибки','Некорректные настройки','Груз не найден','Потеря линии','Не найдена отметка зоны','Не найден круг','Не завершён разворот','Не найдена линия при выезде','Отпущена кнопка груза','Груз не освобождён','Аварийный стоп','Общий тайм-аут','Тайм-аут подъёмника'];
const dirs=['В','СВ','С','СЗ','З','ЮЗ','Ю','ЮВ'];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function defaults(schema){return {values:schema.params.map(p=>p.default),zones:Array.from({length:2},()=>Array.from({length:8},()=>schema.zones.map(z=>z.default))),search:[1,2,3,4,5,6,7],physics:{width:2400,height:1200,leftX:640,rightX:1760,centreY:600,hubRadius:100,lineWidth:30,zoneRadius:Array.from({length:2},()=>Array(8).fill(520)),markerOffset:60,wheelBase:132.38,maxWheelSpeed:300,sensorAhead:60.179,sensorSpacing:16,leftGain:1,rightGain:1,noise:0,seed:1,hubLeft:500,hubRight:720,removeCargo:false,breakLine:false},cargoRay:2};}
function segmentDistance(x,y,a,b){const dx=b.x-a.x,dy=b.y-a.y,q=clamp(((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy),0,1);return Math.hypot(x-a.x-q*dx,y-a.y-q*dy);}
class Simulation{
 constructor(exports,schema,settings){this.w=exports;this.schema=schema;this.index=Object.fromEntries(schema.params.map((p,i)=>[p.key,i]));this.reset(settings);}
 val(k){return this.config.values[this.index[k]];}
 centre(h){return {x:h?this.p.rightX:this.p.leftX,y:this.p.centreY};}
 station(h,r){const c=this.centre(h),a=r*Math.PI/4,n=this.p.zoneRadius[h][r];return {x:c.x+Math.cos(a)*n,y:c.y-Math.sin(a)*n,a};}
 point(forward,left=0){const {x,y,a}=this.robot;return {x:x+Math.cos(a)*forward-Math.sin(a)*left,y:y-Math.sin(a)*forward-Math.cos(a)*left};}
 reset(settings){
  this.config=JSON.parse(JSON.stringify(settings));this.p=this.config.physics;this.w.config_default();this.config.values.forEach((v,i)=>this.w.config_set(i,v));this.config.zones.forEach((r,h)=>r.forEach((z,j)=>z.forEach((v,k)=>this.w.zone_set(h,j,k,v))));this.w.search_count(this.config.search.length);this.config.search.forEach((r,i)=>this.w.search_set(i,r));this.w.reset_robot();
  this.config.cargoOrientation=this.config.cargoOrientation||'horizontal';this.config.forkProfile=this.config.forkProfile||'low';this.configError=this.w.config_error();this.time=0;this.seed=this.p.seed>>>0;this.running=false;this.manual=null;this.manualResult=null;this.trace=[];this.events=[];this.lastState=0;this.liftedEver=false;this.contact=false;this.travel=0;this.wheelTravel=[0,0];
  const h=this.val('START_HUB'),c=this.centre(h);this.robot={x:c.x,y:c.y,a:this.val('START_HEADING')*Math.PI/4};const zone=this.station(h,this.config.cargoRay);this.cargo={x:zone.x,y:zone.y,a:zone.a,z:0,attached:false,localForward:0,localLeft:0,angleOffset:0};this.readings=[0,0,0];this.lines=[];this.buildField();this.sampleSensors();
 }
 buildField(){
  this.lines=[];for(let h=0;h<2;h++){const c=this.centre(h);for(let r=0;r<8;r++){if(r===(h?4:0))continue;const a=r*Math.PI/4,n=this.p.zoneRadius[h][r]-(this.p.markerOffsets?.[h]?.[r]??this.p.markerOffset),cs=Math.cos(a),sn=Math.sin(a),end={x:c.x+cs*n,y:c.y-sn*n};this.lines.push({a:{x:c.x+cs*this.p.hubRadius,y:c.y-sn*this.p.hubRadius},b:end});this.lines.push({a:{x:end.x-sn*((this.p.markerWidth||100)/2),y:end.y-cs*((this.p.markerWidth||100)/2)},b:{x:end.x+sn*((this.p.markerWidth||100)/2),y:end.y+cs*((this.p.markerWidth||100)/2)}});}}
  this.lines.push({a:{x:this.p.leftX+this.p.hubRadius,y:this.p.centreY},b:{x:this.p.rightX-this.p.hubRadius,y:this.p.centreY}});const x=(this.p.leftX+this.p.rightX)/2;this.lines.push({a:{x,y:this.p.centreY-(this.p.crossLength||220)/2},b:{x,y:this.p.centreY+(this.p.crossLength||220)/2}});
 }
 random(){this.seed=(Math.imul(this.seed,1664525)+1013904223)>>>0;return this.seed/4294967296;}
 reflectance(x,y){
  for(let h=0;h<2;h++){const c=this.centre(h);if(Math.hypot(x-c.x,y-c.y)<=this.p.hubRadius)return h?this.p.hubRight:this.p.hubLeft;}
  if(this.p.breakLine&&x>this.p.leftX+185&&x<this.p.leftX+245&&Math.abs(y-this.p.centreY)<60)return 0;
  return this.lines.some(l=>segmentDistance(x,y,l.a,l.b)<=this.p.lineWidth/2)?1000:0;
 }
 sampleSensors(){
  this.sensorPoints=[this.point(this.p.sensorAhead,this.p.sensorSpacing),this.point(this.p.sensorAhead),this.point(this.p.sensorAhead,-this.p.sensorSpacing)];this.readings=this.sensorPoints.map(p=>{let value=0;for(const [dx,dy]of [[0,0],[1.7,0],[-1.7,0],[0,1.7],[0,-1.7]])value+=this.reflectance(p.x+dx,p.y+dy)/5;return Math.round(clamp(value+(this.random()*2-1)*this.p.noise,0,1000));});
  const h=this.liftHeight(),probe=this.point(105.622),c=this.cargo,co=Math.cos(this.robot.a),si=Math.sin(this.robot.a),dx=c.x-probe.x,dy=c.y-probe.y,forward=dx*co-dy*si,left=-dx*si-dy*co,dz=17+h-(20+c.z),radius=8;
  if(this.config.cargoOrientation==='vertical'){const z=17+h-c.z;this.contact=!this.p.removeCargo&&Math.abs(left)<radius&&z>=15&&z<=55&&forward>=-2&&forward<=Math.sqrt(radius*radius-left*left)+1.5;}
  else this.contact=!this.p.removeCargo&&Math.abs(left)<18&&Math.abs(dz)<radius&&forward>=-2&&forward<=Math.sqrt(radius*radius-dz*dz)+1.5;
  this.hubMatch=[0,1].map(h=>{const target=h?this.p.hubRight:this.p.hubLeft;return this.readings.every(v=>Math.abs(v-target)<=this.val('HUB_TOLERANCE'));});
 }
 servoAngle(){return this.manual?this.manual.servo:this.w.get_servo();}
 motorValues(){return this.manual?[this.manual.left,this.manual.right]:[this.w.get_left(),this.w.get_right()];}
 liftHeight(){return 18*(Math.cos(20*Math.PI/180)-Math.cos(this.servoAngle()*Math.PI/180));}
 beginManual(){if(this.configError||(!this.manual&&(this.running||this.w.get_state()!==0)))throw Error('Сначала сбросьте заезд');if(!this.manual)this.manual={servo:this.w.get_servo(),goal:this.w.get_servo(),left:0,right:0,wantLeft:0,wantRight:0,until:this.time,lastMotor:this.time,lastServo:this.time};return this.manual;}
 manualStop(){if(!this.manual)return;const m=this.manual;m.left=m.right=m.wantLeft=m.wantRight=0;m.goal=m.servo;m.until=this.time;this.running=false;this.finishManualTrial(true);}
 manualServo(angle){const m=this.beginManual();if(!Number.isInteger(angle)||angle<this.val('LIFT_LOW')||angle>this.val('LIFT_HIGH'))throw Error('Угол вне настроенного диапазона вил');this.manualStop();m.goal=angle;this.running=m.goal!==m.servo;}
 manualJog(left,right,duration){if(!Number.isInteger(duration)||duration<1||duration>2000||![left,right].every(x=>Number.isInteger(x)&&Math.abs(x)<=150))throw Error('Проба: PWM до 150, время до 2000 мс');const m=this.beginManual();this.manualStop();m.wantLeft=left;m.wantRight=right;m.until=this.time+duration;m.lastMotor=this.time;m.trial={x:this.robot.x,y:this.robot.y,a:this.robot.a,time:this.time,travel:this.travel,left,right,duration};this.manualResult=null;this.running=true;}
 finishManualTrial(stopped=false){const m=this.manual;if(!m?.trial)return;const t=m.trial;this.manualResult={...t,elapsedMs:this.time-t.time,distanceMm:this.travel-t.travel,displacementMm:Math.hypot(this.robot.x-t.x,this.robot.y-t.y),angleDeg:(this.robot.a-t.a)*180/Math.PI,loaded:this.cargo.attached,stopped};delete m.trial;}
 pickupSlack(){return this.config.cargoOrientation==='vertical'?55-(this.config.forkProfile==='high'?32:6):6;}
 start(){if(this.configError||this.manual)return false;this.running=!!this.w.start_robot(this.time);return this.running;}
 tick(dt=.005){
  if(!this.running)return;this.time+=Math.round(dt*1000);this.sampleSensors();
  if(this.manual){const m=this.manual;if(this.time>=m.until)m.left=m.right=m.wantLeft=m.wantRight=0;if(this.time-m.lastMotor>=this.val('RAMP_MS')){m.lastMotor=this.time;const ramp=(actual,target)=>{if(actual&&((actual>0)!==(target>0)))target=0;return actual<target?Math.min(target,actual+this.val('RAMP_STEP')):Math.max(target,actual-this.val('RAMP_STEP'));};m.left=ramp(m.left,m.wantLeft);m.right=ramp(m.right,m.wantRight);}if(m.servo!==m.goal&&this.time-m.lastServo>=this.val('SERVO_MS')){m.lastServo=this.time;m.servo+=Math.sign(m.goal-m.servo)*Math.min(Math.abs(m.goal-m.servo),this.val('SERVO_STEP'));}}
  else this.w.robot_tick(this.time,...this.readings,+this.hubMatch[0],+this.hubMatch[1],+this.contact,0);
  const loadFactor=this.cargo.attached?(this.p.loadedGain??1):1;
  const effective=(u,trim,invert,gain)=>clamp(u*trim/1000*(invert?-1:1),-255,255)/255*this.p.maxWheelSpeed*gain*loadFactor;
  const commands=this.motorValues(),l=effective(commands[0],this.val('LEFT_TRIM'),this.val('LEFT_REVERSE'),this.p.leftGain),r=effective(commands[1],this.val('RIGHT_TRIM'),this.val('RIGHT_REVERSE'),this.p.rightGain),speed=(l+r)/2,pivot=l*r<=0&&l!==r,turnFactor=pivot?(this.p.turnGain??1)*(this.cargo.attached?(this.p.loadedTurnGain??1):1):1,omega=(r-l)/this.p.wheelBase*turnFactor;
  this.wheelTravel[0]+=l*dt;this.wheelTravel[1]+=r*dt;const a=this.robot.a+omega*dt/2;this.robot.x+=Math.cos(a)*speed*dt;this.robot.y-=Math.sin(a)*speed*dt;this.robot.a+=omega*dt;this.travel+=Math.abs(speed*dt);
  const c=this.cargo,h=this.liftHeight();
  const slack=this.pickupSlack(),vertical=this.config.cargoOrientation==='vertical',compatible=vertical||this.config.forkProfile!=='high';
  if(!c.attached&&!this.p.removeCargo&&compatible&&h>=slack){const dx=c.x-this.robot.x,dy=c.y-this.robot.y,forward=dx*Math.cos(this.robot.a)-dy*Math.sin(this.robot.a),left=-dx*Math.sin(this.robot.a)-dy*Math.cos(this.robot.a),aligned=Math.abs(Math.sin(c.a-this.robot.a))<.25;if(forward>92&&forward<129&&Math.abs(left)<(vertical?2:4)&&aligned){c.attached=true;c.localForward=forward;c.localLeft=left;c.angleOffset=c.a-this.robot.a;}}
  if(c.attached){const q=this.point(c.localForward,c.localLeft);c.x=q.x;c.y=q.y;c.a=this.robot.a+c.angleOffset;c.z=Math.max(0,h-slack);if(c.z>1)this.liftedEver=true;if(h<slack-.05){c.attached=false;c.z=0;}}
  if(this.time%100===0)this.trace.push({x:this.robot.x,y:this.robot.y,loaded:this.cargo.attached});
  if(this.manual){this.sampleSensors();if(this.time>=this.manual.until&&this.manual.servo===this.manual.goal){this.running=false;this.finishManualTrial();}return;}
  const state=this.w.get_state();if(state!==this.lastState){this.events.push({time:this.time,state,hub:this.w.get_hub(),ray:this.w.get_ray()});this.lastState=state;}
  if(state===16||state===17)this.running=false;
 }
 abort(){if(this.manual){this.manualStop();return;}this.w.robot_tick(this.time,...this.readings,+this.hubMatch[0],+this.hubMatch[1],+this.contact,1);this.running=false;}
 success(){const dest=this.station(1-this.val('START_HUB'),this.val('DROP_RAY'));const dx=this.cargo.x-dest.x,dy=this.cargo.y-dest.y,radial=dx*Math.cos(dest.a)-dy*Math.sin(dest.a),tangent=-dx*Math.sin(dest.a)-dy*Math.cos(dest.a);return this.w.get_state()===16&&this.liftedEver&&!this.cargo.attached&&Math.abs(radial)<=((this.p.zoneSize||100)-40)/2&&Math.abs(tangent)<=((this.p.zoneSize||100)-100)/2+(this.config.cargoOrientation==='vertical'?30:15);}
}
global.RadialSim={Simulation,defaults,names,faults,dirs,clamp};if(typeof module!=='undefined')module.exports=global.RadialSim;
})(typeof globalThis!=='undefined'?globalThis:this);
