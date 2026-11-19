window.setupAmurSerial=function({getCfg,configError,base,meta,download,projectConfig}){
 const $=id=>document.getElementById(id),pane=$('pane-arduino');pane.innerHTML='<h2>Arduino UNO / Nano</h2><div class="form-row"><label for="boardProfile">Какая плата?</label><select id="boardProfile"><option value="uno">UNO · Optiboot</option><option value="uno-auto">UNO · не знаю загрузчик</option><option value="uno-old">UNO · 57600</option><option value="nano-auto">Nano · не знаю загрузчик</option><option value="nano-old">Nano · старый, 57600</option><option value="nano-new">Nano · новый, 115200</option></select></div><p class="hint" id="boardHelp"></p><label class="hint"><input type="checkbox" id="manualReset"> Сброс кнопкой RESET</label><p class="hint">Если плата не отвечает: закройте монитор порта и Arduino IDE, отключите всё от D0/RX и D1/TX. Включите сброс кнопкой и нажмите RESET, когда появится подсказка. Если COM-порта нет — проверьте USB-кабель и драйвер USB-чипа вашей платы.</p><p class="hint">В плату попадёт программа с вашими настройками. На роботе проверьте датчики и время движений.</p><p class="hint">Перед записью отключите моторы. Поддерживаются UNO и классическая Nano на ATmega328P, 16 МГц.</p><div class="export-buttons"><button id="flashUno" class="primary">Записать программу по USB</button><button id="cancelFlash" disabled>Остановить запись</button><button id="downloadHex">↓ HEX с текущими настройками</button></div><progress id="flashProgress" max="100" value="0" style="width:100%;margin-top:14px"></progress><p class="hint" id="serialSupport"></p><pre id="serialLog" class="serial-log"></pre><div class="section"><h2>Настроить датчики</h2><div class="inline"><button id="openMonitor">Подключить</button><button id="closeMonitor" disabled>Отключить</button></div><div class="cal-buttons" id="calButtons"></div><form id="serialForm" class="inline" style="margin-top:10px"><input id="serialCommand" aria-label="Команда Arduino" placeholder="status" style="min-width:0;width:100%"><button>Отправить</button></form><p class="hint">Все три датчика — над одним покрытием. Нажмите его название. Дождитесь CAL SAMPLE OK. Повторите для остальных покрытий, затем «Сохранить».</p></div>';
 const real=document.createElement('div');real.className='section';real.innerHTML='<h2>Проверка настоящего робота по USB</h2><p class="hint">Ниже команды для подключённой платы. Моторные пробы: вилы внизу, груз снят. Сначала «Подключить», затем «Разрешить пробы». После «Стоп» — опустите вилы, «Сброс», снова разрешите пробы.</p><div class="form-row"><label for="realPwm">PWM · 1–150</label><input id="realPwm" type="number" min="1" max="150" step="1" value="85"></div><div class="form-row"><label for="realDuration">Время пробы · 50–2000 мс</label><input id="realDuration" type="number" min="50" max="2000" step="10" value="1000"></div><div id="realControls" class="cal-buttons"></div>';
 const direction=document.createElement('div');direction.className='section';direction.innerHTML='<h2>Направление SG90</h2><p class="hint">Если настоящая качалка движется противоположно модели: сначала запишите обновлённую прошивку. Снимите качалку, подключите монитор, нажмите «Опустить» и дождитесь остановки. При ошибке состояния нажмите «Сброс».</p><div class="form-row"><label for="servoDirection">Направление настоящего серво</label><select id="servoDirection"><option value="normal">Обычное</option><option value="reverse">Обратное</option></select></div><label class="check"><input id="servoDetached" type="checkbox">Качалка снята, серво без нагрузки</label><button id="applyServoDirection" disabled>Сохранить направление в Arduino</button><p class="hint" id="servoDirectionStatus">Текущее направление: нажмите «Статус». servo_reverse=1 — обратное. После сохранения выключите питание и установите качалку в нижнее положение по рисунку. Настройка хранится в EEPROM платы, отдельно от HTML.</p>';
 real.append(direction);const powerNote=document.createElement('p');powerNote.className='hint';powerNote.textContent='Для USB-проб отсоедините внешний провод 5 В от Arduino: плата питается от USB, моторы и серво — от своих источников. Общий GND оставьте соединённым.';real.append(powerNote);pane.append(real);
 const projectButton=document.createElement('button');projectButton.id='downloadProject';projectButton.textContent='↓ Скачать проект Arduino (ZIP)';$('downloadHex').after(projectButton);
 projectButton.onclick=()=>{try{if(configError())throw Error('Сначала исправьте настройки программы');const blob=AmurProject.build(projectConfig(),getCfg().uploadBoard||'uno'),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Pogruzchik_Arduino_Project.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);log('Проект скачан. Распакуйте ZIP и откройте RadialRobot.ino в Arduino IDE.');}catch(e){log(e.message);}};
 const connection=document.querySelector('#openMonitor').parentElement;
 const sensors=$('calButtons').parentElement;
 sensors.querySelector('h2').remove();
 const calibrationFeedback=document.createElement('p');
 calibrationFeedback.id='calibrationFeedback';
 calibrationFeedback.setAttribute('aria-live','polite');
 sensors.append(calibrationFeedback);
 const flashing=document.createElement('div');
 for(const element of [...pane.children]){
  if(element===$('serialSupport'))break;
  flashing.append(element);
 }
 const section=(label,node,open=false)=>{
  const details=document.createElement('details');
  const title=document.createElement('summary');
  title.textContent=label;
  details.open=open;
  details.append(title,node);
  return details;
 };
 const controls=document.createElement('div');
 controls.innerHTML=`
   <p>Сними груз. Подводи механизм к нужной высоте шагами по 1°.</p>
   <p class="hint">Угол на экране — команда Arduino. Положение вил проверь на роботе.</p>
   <p id="liveHardware" aria-live="polite">Нажми «Статус» или включи телеметрию.</p>
   <div class="cal-buttons">
    <button data-command="status">Статус</button>
    <button data-command="stream on">Телеметрия вкл.</button>
    <button data-command="stream off">Телеметрия выкл.</button>
    <button data-command="stop" class="danger">Стоп</button>
   </div>
 `;
 const limits=document.createElement('div');
 limits.innerHTML=`
   <h2>Положения вил</h2>
   <div class="form-row"><label for="servoTarget">Пробный угол (0–180°)</label><input id="servoTarget" type="number" min="0" max="180"></div>
   <div class="cal-buttons">
    <button id="servoBack">−1°</button><button id="servoForward">+1°</button><button id="servoPreview">Перейти к углу</button>
    <button data-command="low">Вниз</button><button data-command="high">Вверх</button>
   </div>
   <div class="form-row"><label for="servoLow">Нижний угол</label><input id="servoLow" type="number" min="0" max="179"><button id="captureLow">Взять текущий</button></div>
   <div class="form-row"><label for="servoHigh">Верхний угол</label><input id="servoHigh" type="number" min="1" max="180"><button id="captureHigh">Взять текущий</button></div>
   <button id="saveServoLimits">Сохранить оба в Arduino</button>
   <p class="hint" id="servoLimitsStatus">Для калибровки нужна обновлённая прошивка. Сохранённые углы действуют и в автоматическом заезде.</p>
 `;
 const terminal=document.createElement('div');
 const diagnosticsNote=document.createElement('p');
 diagnosticsNote.className='hint';
 diagnosticsNote.textContent='Для реальной калибровки включите «Телеметрия вкл.», проведите короткую безопасную пробу и сохраните журнал. В нём есть значения трёх LDR, PWM колёс, ошибка линии и длительность её потери.';
 terminal.append(diagnosticsNote);
 terminal.append($('serialLog'),$('serialForm'));
 const clearLog=document.createElement('button');
 clearLog.textContent='Очистить журнал';
 clearLog.onclick=()=>$('serialLog').textContent='';
 terminal.append(clearLog);
 const saveLog=document.createElement('button');
 saveLog.id='saveHardwareLog';saveLog.textContent='↓ Скачать журнал диагностики';
 saveLog.onclick=()=>{
  const content=$('serialLog').textContent.trim();
  if(!content){log('Журнал пуст. Сначала включите телеметрию.');return;}
  const name='AmurCargo_Diagnostics_'+new Date().toISOString().replace(/[:.]/g,'-')+'.txt';
  const url=URL.createObjectURL(new Blob([content+'\n'],{type:'text/plain;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 terminal.append(saveLog);
 const directionSection=section('Направление SG90',direction);
 limits.append(directionSection);
 const heading=document.createElement('h2');
 heading.textContent='Реальный робот';
 const portStatus=document.createElement('p');
 portStatus.id='portStatus';
 pane.replaceChildren(heading,$('serialSupport'),connection,portStatus,controls,
  section('Сервопривод',limits,true),section('Датчики',sensors),
  section('Проба моторов',real),section('Прошивка',flashing),section('Терминал COM',terminal));
 let telemetry=null,limitsLoaded=false;
 let busy=false,controller=null,monitor=null,openingMonitor=false;
 const telemetryPlaceholders=Object.fromEntries(
  ['liveHardware','servoLimitsStatus','servoDirectionStatus'].map(id=>[id,$(id).textContent])
 );
 const log=s=>{$('serialLog').textContent=($('serialLog').textContent+'\n'+s).slice(-10000);$('serialLog').scrollTop=$('serialLog').scrollHeight;const status=String(s).match(/angle=(\d+).*?servo_output=(\d+).*?servo_goal=(\d+).*?servo_low=(\d+).*?servo_high=(\d+).*?start_button=(\d).*?raw=([^=]+?) line=.*?contact=(\d)/);
 if(status){
  const [angle,physical,goal,low,high,start,raw,contact]=status.slice(1);
  telemetry={angle:Number(angle),goal:Number(goal)};
  const diag=String(s).match(/pwm=(-?\d+)\s+(-?\d+)\s+target=(-?\d+)\s+(-?\d+)\s+err=(-?\d+)\s+corr=(-?\d+)\s+dfilter=(-?\d+)\s+lost_ms=(\d+)\s+cal=(\d+)/);
  const navigation=diag?` · PWM ${diag[1]}/${diag[2]} (цель ${diag[3]}/${diag[4]}) · ошибка ${diag[5]} · коррекция ${diag[6]} · потеря ${diag[8]} мс · калибровка ${diag[9]==='0'?'готова':diag[9]==='1'?'неполная':'круги неразличимы'}`:'';
  $('liveHardware').textContent=`Серво ${angle}° → ${goal}° · выход ${physical}° · датчики ${raw.trim()} · старт ${start==='1'?'нажата':'отпущена'} · груз ${contact==='1'?'есть':'нет'}${navigation}`;
  $('servoLimitsStatus').textContent=`В Arduino сохранены рабочие положения ${low}° и ${high}°.`;
  if(!limitsLoaded||String(s).includes('SERVO LIMITS SAVED')){
   $('servoLow').value=low;$('servoHigh').value=high;$('servoTarget').value=goal;
   limitsLoaded=true;
  }
  buttons();
 }
 if(String(s).startsWith('SERVO REFUSED')||String(s).startsWith('BUSY')||String(s).startsWith('RESET REQUIRED'))$('servoLimitsStatus').textContent=s;
 if(s.startsWith('CAL HUB OVERLAP'))$('calibrationFeedback').textContent='Показания кругов перекрываются. Снимите образцы левого и правого кругов заново.';
 if(s.startsWith('CAL REQUIRED'))$('calibrationFeedback').textContent='Снимите образцы белого, чёрного и требуемых кругов.';
 if(s.startsWith('CAL SAMPLE OK')||s==='EEPROM SAVED')$('calibrationFeedback').textContent=s==='EEPROM SAVED'?'Калибровка сохранена.':'Образец записан. После завершения нажмите «Сохранить».';
 if(String(s)==='SERVO LIMITS SAVED'){limitsLoaded=false;$('servoLimitsStatus').textContent='Положения записаны в Arduino.';}
 if(s.startsWith('RADIAL READY'))send('status').catch(e=>log(e.message));
 const match=String(s).match(/(?:servo_reverse|SERVO SAVED reverse)=(0|1)/);if(match){if(String(s).startsWith('SERVO SAVED')){limitsLoaded=false;}$('servoDirection').value=match[1]==='1'?'reverse':'normal';$('servoDirectionStatus').textContent='Плата сообщает: '+(match[1]==='1'?'обратное':'обычное')+' направление SG90. Сохранено в EEPROM. Установите качалку в нижнем положении при выключенном питании.';}};
 const supported=!!navigator.serial&&isSecureContext;
 $('serialSupport').textContent=supported?'USB доступен. Выберите плату в окне браузера.':('USB здесь недоступен. Откройте файл в Chrome или Edge. Если не помогло — попросите наставника открыть страницу через HTTPS или localhost.');
 function syncBoard(){const raw=getCfg().uploadBoard,key=typeof raw==='string'&&AmurFlash.profiles[raw]?raw:'uno';getCfg().uploadBoard=key;$('boardProfile').value=key;$('boardHelp').textContent=key.startsWith('nano')?'У китайской Nano могут быть разные загрузчики. Не знаете — выберите автоподбор. CH340 не указывает тип загрузчика.':'Обычная UNO: 115200. Для неизвестного загрузчика выберите автоподбор. Происхождение платы и USB-чип не определяют загрузчик; поддерживается ATmega328P, 16 МГц.';} $('boardProfile').onchange=()=>{getCfg().uploadBoard=$('boardProfile').value;syncBoard();};syncBoard();
 function buttons(){
  const connected=!!monitor&&!monitor.closing;
  const locked=busy||openingMonitor||!!monitor;
  $('flashUno').disabled=$('openMonitor').disabled=!supported||locked;
  $('closeMonitor').disabled=!connected;
  $('cancelFlash').disabled=!controller;
  $('downloadHex').disabled=busy;
  $('boardProfile').disabled=$('manualReset').disabled=locked;
  $('applyServoDirection').disabled=!connected||!$('servoDetached').checked;
  $('portStatus').textContent=connected?'COM-порт подключён · 115200 бод':'COM-порт отключён';
  for(const button of pane.querySelectorAll('[data-command],[data-real-command],[data-real-jog],#calButtons button,#serialForm button'))button.disabled=!connected;
  for(const id of ['servoBack','servoForward','servoPreview','captureLow','captureHigh','saveServoLimits'])$(id).disabled=!connected||!telemetry;
 }
 function image(){if(configError())throw Error('Сначала исправьте настройки программы');return AmurFlash.patch(base,AmurFlash.boardMeta(meta,getCfg().uploadBoard||'uno'),getCfg());}
 $('downloadHex').onclick=()=>{try{download((getCfg().uploadBoard||'uno').startsWith('nano')?'Pogruzchik_NANO.hex':'Pogruzchik_UNO.hex',AmurFlash.hex(image()));log('HEX сформирован с текущими настройками.');}catch(e){log(e.message);}};
 $('flashUno').onclick=async()=>{if(busy||openingMonitor||monitor)return;busy=true;buttons();try{const firmware=image(),key=getCfg().uploadBoard||'uno',port=await navigator.serial.requestPort();controller=new AbortController();buttons();await AmurFlash.uploadBoard(port,firmware,meta,key,(p,s)=>{$('flashProgress').value=p;log(s);},controller.signal,$('manualReset').checked);}catch(e){log(e.name==='NotFoundError'?'Порт не выбран. В окне браузера нажмите на свою плату / COM-порт, затем «Подключить».':e.name==='NetworkError'?'Не удалось открыть порт. Закройте Arduino IDE и другие вкладки с подключением к плате.':'Загрузка: '+e.message);}finally{busy=false;controller=null;buttons();}};
 $('cancelFlash').onclick=()=>controller?.abort();
 function clearTelemetry(){
  telemetry=null;limitsLoaded=false;
  for(const [id,message] of Object.entries(telemetryPlaceholders))$(id).textContent=message;
  for(const id of ['servoLow','servoHigh','servoTarget'])$(id).value='';
  $('calibrationFeedback').textContent='';
  $('servoDetached').checked=false;
  $('servoDirection').value='normal';
 }
 async function releaseMonitor(session){
  session.closing=true;clearTelemetry();buttons();
  session.reader?.releaseLock();
  session.writer?.releaseLock();
  try{await session.port.close();}
  catch(e){log('Порт: '+e.message);}
  finally{monitor=null;buttons();}
 }
 async function readMonitor(session){
  const decoder=new TextDecoder();
  let incoming='';
  try{
   while(!session.closing){
    const {value,done}=await session.reader.read();
    if(done||session.closing)break;
    incoming+=decoder.decode(value,{stream:true});
    let at;
    while((at=incoming.indexOf('\n'))>=0){
     log(incoming.slice(0,at).replace(/\r$/,''));
     incoming=incoming.slice(at+1);
    }
    if(incoming.length>2048){log(incoming);incoming='';}
   }
  }catch(e){if(!session.closing)log('Порт: '+e.message);}
  finally{await releaseMonitor(session);}
 }
 $('openMonitor').onclick=async()=>{
  if(busy||openingMonitor||monitor)return;
  openingMonitor=true;buttons();
  try{
   const port=await navigator.serial.requestPort();
   await port.open({baudRate:115200});
   const session={port,closing:false};
   monitor=session;
   try{
    session.reader=port.readable.getReader();
    session.writer=port.writable.getWriter();
   }catch(e){await releaseMonitor(session);throw e;}
   session.pump=readMonitor(session);
   log('Монитор подключён, 115200 бод.');
  }catch(e){log('Подключение: '+e.message);}
  finally{openingMonitor=false;buttons();}
 };
 $('closeMonitor').onclick=async()=>{
  const session=monitor;
  if(!session||session.closing)return;
  session.closing=true;clearTelemetry();buttons();
  try{await session.reader.cancel();}
  catch(e){log('Порт: '+e.message);}
  await session.pump;
 };
 async function send(command){
  if(!monitor?.writer||monitor.closing){log('Сначала подключите монитор порта.');return;}
  if(command.length>70||/[\r\n]/.test(command)){log('Недопустимая команда');return;}
  await monitor.writer.write(new TextEncoder().encode(command+'\n'));
  log('> '+command);
 }
 $('servoDetached').onchange=buttons;$('applyServoDirection').onclick=()=>{if(!monitor||monitor.closing||!$('servoDetached').checked)return;const mode=$('servoDirection').value;if(!['normal','reverse'].includes(mode))return;send('servo '+mode+' detached').catch(e=>log(e.message));$('servoDetached').checked=false;buttons();};
 for(const [label,command]of [['Разрешить пробы','arm'],['↑ Поднять вилы','high'],['↓ Опустить вилы','low'],['Сброс','reset'],['■ Стоп','stop']]){const b=document.createElement('button');b.textContent=label;b.dataset.realCommand=command;b.onclick=()=>send(command).catch(e=>log(e.message));$('realControls').append(b);}
 for(const [label,l,r]of [['↑ Вперёд',1,1],['↓ Назад',-1,-1],['↶ Влево',-1,1],['↷ Вправо',1,-1]]){const b=document.createElement('button');b.textContent=label;b.dataset.realJog=l+','+r;b.onclick=()=>{const p=Number($('realPwm').value),t=Number($('realDuration').value);if(!Number.isInteger(p)||p<1||p>150||!Number.isInteger(t)||t<50||t>2000){log('PWM: 1–150; время: 50–2000 мс.');return;}send('jog '+l*p+' '+r*p+' '+t).catch(e=>log(e.message));};$('realControls').append(b);}
 const command=s=>{
  if(telemetry && /^(angle |low$|high$|stop$)/.test(s))telemetry.angle=null;
  send(s).catch(e=>log(e.message));
 };
 for(const button of pane.querySelectorAll('[data-command]'))button.onclick=()=>command(button.dataset.command);
 const angle=id=>$(id).value===''?NaN:Number($(id).value);
 const preview=value=>{
  if(Number.isInteger(value)&&value>=0&&value<=180){$('servoTarget').value=value;telemetry.goal=value;command('angle '+value);}
  else $('servoLimitsStatus').textContent='Укажи целый угол от 0 до 180°.';
 };
 $('servoPreview').onclick=()=>preview(angle('servoTarget'));
 $('servoBack').onclick=()=>preview(telemetry.goal-1);
 $('servoForward').onclick=()=>preview(telemetry.goal+1);
 for(const [button,input] of [['captureLow','servoLow'],['captureHigh','servoHigh']]){
  $(button).onclick=()=>{
   if(telemetry.angle===null||telemetry.angle!==telemetry.goal){$('servoLimitsStatus').textContent='Дождись остановки и нажми «Статус» или включи телеметрию.';return;}
   $(input).value=telemetry.angle;
  };
 }
 $('saveServoLimits').onclick=()=>{
  const low=angle('servoLow'),high=angle('servoHigh');
  if(!Number.isInteger(low)||!Number.isInteger(high)||low<0||high>180||low>=high){
   $('servoLimitsStatus').textContent='Нижний угол должен быть меньше верхнего. Допустимый диапазон 0–180°.';return;
  }
  command('limits '+low+' '+high);
 };
 $('serialForm').onsubmit=e=>{e.preventDefault();send($('serialCommand').value.trim()).catch(e=>log(e.message));};
 for(const[label,command]of [['Белое','cal white'],['Чёрное','cal black'],['Левый круг','cal left'],['Правый круг','cal right'],['Сохранить','save'],['Статус','status'],['Поток','stream'],['Опустить','low'],['Стоп','stop']]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>send(command).catch(e=>log(e.message));$('calButtons').append(b);}buttons();return {image,syncBoard,get busy(){return busy;}};
};
