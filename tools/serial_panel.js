window.setupAmurSerial=function({getCfg,configError,base,meta,download,projectConfig,schema}){
 const $=id=>document.getElementById(id),pane=$('pane-arduino');pane.innerHTML='<h2>Arduino UNO / Nano</h2><div class="form-row"><label for="boardProfile">Какая плата?</label><select id="boardProfile"><option value="uno">UNO · Optiboot</option><option value="uno-auto">UNO · не знаю загрузчик</option><option value="uno-old">UNO · 57600</option><option value="nano-auto">Nano · не знаю загрузчик</option><option value="nano-old">Nano · старый, 57600</option><option value="nano-new">Nano · новый, 115200</option></select></div><p class="hint" id="boardHelp"></p><label class="hint"><input type="checkbox" id="manualReset"> Сброс кнопкой RESET</label><p class="hint">Если плата не отвечает: закройте монитор порта и Arduino IDE, отключите всё от D0/RX и D1/TX. Включите сброс кнопкой и нажмите RESET, когда появится подсказка. Если COM-порта нет — проверьте USB-кабель и драйвер USB-чипа вашей платы.</p><p class="hint">В плату попадёт программа с вашими настройками. На роботе проверьте датчики и время движений.</p><p class="hint">Перед записью отключите моторы. Поддерживаются UNO и классическая Nano на ATmega328P, 16 МГц.</p><div class="export-buttons"><button id="flashUno" class="primary">Записать программу по USB</button><button id="cancelFlash" disabled>Остановить запись</button><button id="downloadHex">↓ HEX с текущими настройками</button></div><progress id="flashProgress" max="100" value="0" style="width:100%;margin-top:14px"></progress><p class="hint" id="serialSupport"></p><pre id="serialLog" class="serial-log"></pre><div class="section"><h2>Настроить датчики</h2><div class="inline"><button id="openMonitor">Подключить</button><button id="closeMonitor" disabled>Отключить</button></div><div class="cal-buttons" id="calButtons"></div><form id="serialForm" class="inline" style="margin-top:10px"><input id="serialCommand" aria-label="Команда Arduino" placeholder="status" style="min-width:0;width:100%"><button>Отправить</button></form><p class="hint">Все три датчика — над одним покрытием. Нажмите его название. Дождитесь CAL SAMPLE OK. Повторите для остальных покрытий, затем «Сохранить».</p></div>';
 const real=document.createElement('div');real.className='section';real.innerHTML='<h2>Проверка настоящего робота по USB</h2><p class="hint">Ниже команды для подключённой платы. Моторные пробы: вилы внизу, груз снят. Сначала «Подключить», затем «Разрешить пробы». После «Стоп» — опустите вилы, «Сброс», снова разрешите пробы.</p><div class="form-row"><label for="realLeftPwm">Левый PWM · 0–255</label><input id="realLeftPwm" type="number" min="0" max="255" value="85"></div><div class="form-row"><label for="realRightPwm">Правый PWM · 0–255</label><input id="realRightPwm" type="number" min="0" max="255" value="85"></div><p class="hint">Проба подаёт указанный PWM сразу, без разгона, минимума и баланса. Это позволяет измерить реальный порог запуска каждого колеса. Если даже PWM 255 не вращает вывешенное колесо, проверьте отдельное питание моторов и клеммы шилда.</p><div class="form-row"><label for="realDuration">Время пробы · 50–2000 мс</label><input id="realDuration" type="number" min="50" max="2000" step="10" value="1000"></div><label class="check"><input id="realUseKick" type="checkbox"> Сначала пусковой толчок, затем удержание заданного PWM</label><div class="form-row"><label for="realKickPwm">PWM толчка · 1–255</label><input id="realKickPwm" type="number" min="1" max="255" value="145"></div><div class="form-row"><label for="realKickMs">Длительность толчка · 1–150 мс</label><input id="realKickMs" type="number" min="1" max="150" value="60"></div><p class="hint">Сначала PWM толчка, затем указанный слева/справа PWM непрерывно до конца пробы. Параметры этой пробы не меняют EEPROM. Уменьшайте рабочий PWM по 5–10 и смотрите, продолжает ли колесо вращаться без остановки.</p><p class="hint" id="realProbeStatus">Пробы без толчка измеряют стартовый порог; с толчком — минимальный удерживаемый PWM.</p><div id="realControls" class="cal-buttons"></div>';
 
 const motorDefs=[
  ['motorMinLeft','Левый: минимальный PWM',0,255,70],['motorMinRight','Правый: минимальный PWM',0,255,70],
  ['motorTrimLeft','Левый: баланс /1000',500,1500,1000],['motorTrimRight','Правый: баланс /1000',500,1500,1000],
  ['motorDrive','По линии без груза',20,220,85],['motorLoaded','По линии с грузом',20,220,75],
  ['motorApproach','Подъезд / отход',15,180,55],['motorCentre','Подъезд к центру',15,180,80],
  ['motorTurn','Поворот без груза',20,200,85],['motorTurnLoaded','Поворот с грузом',20,200,75],
  ['motorRampStep','Шаг плавного разгона',1,255,5],['motorRampMs','Интервал разгона, мс',1,100,10]
 ];
 const dynamicsDefs=[
  ['motorKickPwm','Стартовый толчок: PWM (0 = выкл.)',0,255,0],
  ['motorKickMs','Длительность толчка, мс',0,150,0]
 ];
 const motor=document.createElement('div');
 motor.innerHTML='<h2>Скорости и пороги запуска</h2><p class="hint">Ненулевые команды ниже минимального PWM поднимаются до порога, а команда 0 всегда останавливает мотор. Баланс 1000 = 100%.</p>'+
  motorDefs.map(([id,label,min,max,value])=>'<div class="form-row"><label for="'+id+'">'+label+'</label><input id="'+id+'" type="number" min="'+min+'" max="'+max+'" step="1" value="'+value+'"></div>').join('')+
  '<div class="cal-buttons"><button id="motorApply">Применить в Arduino</button></div><h3>Пусковой толчок</h3>'+
  '<p class="hint">После стартового толчка колёса работают с непрерывным PWM. Минимальный рабочий PWM настраивается отдельно для каждого колеса.</p>'+
  dynamicsDefs.map(([id,label,min,max,value])=>'<div class="form-row"><label for="'+id+'">'+label+'</label><input id="'+id+'" type="number" min="'+min+'" max="'+max+'" step="1" value="'+value+'"></div>').join('')+
  '<div class="cal-buttons"><button id="motorDynamicsApply">Применить толчок</button><button id="motorSave">Сохранить всё в EEPROM</button><button id="motorClear">Очистить EEPROM моторов</button></div><p class="hint" id="motorConfigStatus">Нужна обновлённая прошивка. Применить — временно; после проверки нажмите «Сохранить в EEPROM».</p>';
 const direction=document.createElement('div');direction.className='section';direction.innerHTML='<h2>Направление SG90</h2><p class="hint">Если настоящая качалка движется противоположно модели: сначала запишите обновлённую прошивку. Снимите качалку, подключите монитор, нажмите «Опустить» и дождитесь остановки. При ошибке состояния нажмите «Сброс».</p><div class="form-row"><label for="servoDirection">Направление настоящего серво</label><select id="servoDirection"><option value="normal">Обычное</option><option value="reverse">Обратное</option></select></div><label class="check"><input id="servoDetached" type="checkbox">Качалка снята, серво без нагрузки</label><button id="applyServoDirection" disabled>Сохранить направление в Arduino</button><p class="hint" id="servoDirectionStatus">Текущее направление: нажмите «Статус». servo_reverse=1 — обратное. После сохранения выключите питание и установите качалку в нижнее положение по рисунку. Настройка хранится в EEPROM платы, отдельно от HTML.</p>';
 const powerNote=document.createElement('p');powerNote.className='hint';powerNote.textContent='Для USB-проб отсоедините внешний провод 5 В от Arduino: плата питается от USB, моторы и серво — от своих источников. Общий GND оставьте соединённым.';real.append(powerNote);pane.append(real);
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
   <p class="hint">Это заданный угол, не измеренное положение вала. 0–180° соответствуют импульсам 544–2400 мкс, но механический диапазон SG90 может быть уже. Крайние углы проверяй без качалки и груза.</p>
   <p id="liveHardware" aria-live="polite">Нажмите «Статус» или включите телеметрию.</p>
   <div class="cal-buttons">
    <button data-command="status">Статус</button>
    <button data-command="stream on">Телеметрия вкл.</button>
    <button data-command="stream off">Телеметрия выкл.</button>
    <button data-command="stop" class="danger">Стоп</button>
   </div>
 `;
 const limits=document.createElement('div');
 limits.innerHTML=`
   <p class="hint">Снимите груз перед настройкой. Крайние углы проверяйте со снятой качалкой.</p>
   <div class="form-row"><label for="servoTarget">Пробный угол (0–180°)</label><input id="servoTarget" type="number" min="0" max="180"></div>
   <div class="cal-buttons">
    <button id="servoBack">−1°</button><button id="servoForward">+1°</button><button id="servoPreview">Перейти к углу</button>
    <button data-command="low">Вниз</button><button data-command="high">Вверх</button>
   </div>
   <div class="form-row"><label for="servoLow">Нижний угол</label><input id="servoLow" type="number" min="0" max="179"><button id="captureLow">Взять текущий</button></div>
   <div class="form-row"><label for="servoHigh">Верхний угол</label><input id="servoHigh" type="number" min="1" max="180"><button id="captureHigh">Взять текущий</button></div>
   <button id="saveServoLimits">Сохранить углы в EEPROM</button>
   <p class="hint" id="servoLimitsStatus">Для калибровки нужна обновлённая прошивка. Сохранённые углы действуют и в автоматическом заезде.</p>
 `;
 const terminal=document.createElement('div');
 const diagnosticRows=[];
 let diagnosticStart=null;
 const diagnosticColumns='received_at_utc,elapsed_ms,event,state,fault,ldr_left,ldr_centre,ldr_right,applied_pwm_left,applied_pwm_right,servo_angle,contact,held,line_error,marker,target_pwm_left,target_pwm_right';
 function recordDiagnostic(event,values){
  const received=performance.now();
  diagnosticStart??=received;
  diagnosticRows.push([new Date().toISOString(),Math.round(received-diagnosticStart),event,...values].join(','));
 }
 const diagnosticsNote=document.createElement('p');
 diagnosticsNote.className='hint';
 diagnosticsNote.textContent='Перед заездом нажмите «Очистить журнал» и «Телеметрия вкл.». В CSV попадут все полученные показания и переходы между этапами. Полный отчёт доступен кнопкой «Статус» после остановки.';
 terminal.append(diagnosticsNote);
 terminal.append($('serialLog'),$('serialForm'));
 const clearLog=document.createElement('button');
 clearLog.textContent='Очистить журнал';
 clearLog.onclick=()=>{
  $('serialLog').textContent='';
  diagnosticRows.length=0;
  diagnosticStart=null;
 };
 terminal.append(clearLog);
 const saveLog=document.createElement('button');
 saveLog.id='saveHardwareLog';saveLog.textContent='↓ Скачать журнал диагностики';
 saveLog.onclick=()=>{
  if(!diagnosticRows.length){log('Журнал пуст. Сначала включите телеметрию.');return;}
  const name='AmurCargo_Diagnostics_'+new Date().toISOString().replace(/[:.]/g,'-')+'.csv';
  const url=URL.createObjectURL(new Blob([diagnosticColumns+'\r\n',diagnosticRows.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 terminal.append(saveLog);
 const sound=document.createElement('div');
  sound.innerHTML='<p class="hint">Буззер D4 сигнализирует о старте, зонах, грузе, финише и ошибках. Отключение сохраняется после перезагрузки.</p>'+
   '<div class="cal-buttons"><button data-command="buzzer test">Проверить звук</button><button data-command="buzzer off">Выключить</button><button data-command="buzzer on">Включить</button><button data-command="buzzer status">Состояние</button></div>'+
   '<p class="hint">Тест доступен только при остановке. Выключить звук можно и во время движения.</p>';
  const directionSection=section('Направление SG90',direction);
 limits.append(directionSection);
 const heading=document.createElement('h1');
 heading.textContent='Управление роботом';
 const portStatus=document.createElement('p');
 portStatus.id='portStatus';
 const connectionBar=document.createElement('header');
 connectionBar.className='robot-connection';
 const identity=document.createElement('div');
 identity.append(heading,portStatus);
 connection.append(controls.querySelector('[data-command="stop"]'));
 connectionBar.append(identity,connection);
 const mission=document.createElement('article');
 mission.className='robot-card';
 mission.innerHTML=`
  <h2>Автономный заезд</h2>
  <div class="form-row"><label for="robotMode">Режим</label>
   <select id="robotMode"><option value="full">Поиск и доставка</option><option value="line">По линии до груза</option></select>
  </div>
  <p class="hint" id="robotModeHelp"></p>
  <p class="hint">Без USB удерживайте START 6 секунд и отпустите. Три коротких сигнала после отпускания — «По линии до груза», один длинный — «Поиск и доставка». Для заезда держите START до двух коротких сигналов, отпустите, затем коротко нажмите и отпустите.</p>
  <div class="cal-buttons">
   <button data-command="arm" id="armMission">Разрешить запуск</button>
   <button data-command="start" id="startMission" class="primary">Запустить</button>
   <button data-command="reset">Сбросить</button>
  </div>
  <p id="robotFeedback" role="status">Подключите Arduino, чтобы управлять роботом.</p>
 `;
 const dashboard=document.createElement('div');
 dashboard.className='robot-dashboard';
 controls.className='robot-card';
 controls.querySelectorAll('p:not([id])').forEach(p=>p.remove());
 controls.insertAdjacentHTML('afterbegin',`
  <h2>Состояние робота</h2>
  <div class="robot-readouts">
   <div><span>Этап</span><strong id="robotStage">—</strong></div>
   <div><span>Груз</span><strong id="robotCargo">—</strong></div>
   <div><span>Вилы</span><strong id="robotLift">—</strong></div>
   <div><span>PWM колёс</span><strong id="robotWheels">—</strong></div>
  </div>
 `);
 dashboard.append(mission,controls);
 const settingsLink=document.createElement('button');
 settingsLink.textContent='Открыть параметры для прошивки';
 settingsLink.onclick=()=>document.querySelector('[data-tab="settings"]').click();
 flashing.prepend(settingsLink);
 const flashFeedback=document.createElement('p');
 flashFeedback.className='hint';
 flashFeedback.setAttribute('role','status');
 flashing.append(flashFeedback);
 sensors.insertAdjacentHTML('afterbegin',`
  <div class="form-row"><label for="cargoActiveLevel">Уровень при обнаружении груза</label>
   <select id="cargoActiveLevel"><option value="high">HIGH · 1</option><option value="low">LOW · 0</option></select>
  </div>
  <div class="form-row"><label for="cargoPullup">Подтяжка входа датчика груза</label>
   <select id="cargoPullup"><option value="off">Выключена</option><option value="on">Включена</option></select>
  </div>
  <p class="hint">Изменения датчика груза сохраняются в Arduino сразу.</p>
  <h3>Калибровка отражения</h3>
 `);
 const lineFields=[
  ['LINE_THRESHOLD','Порог чёрной линии'],['KP','Реакция на отклонение (Kp)'],['KD','Демпфирование (Kd)'],
  ['MAX_CORRECTION','Максимальная коррекция PWM'],['LOST_MS','Остановка при потере линии, мс'],
  ['CONTACT_MS','Подтверждение сигнала груза, мс']
 ].map(([key,label])=>({...schema.params.find(p=>p.key===key),label}));
 const tuning=document.createElement('div');
 tuning.innerHTML=`
  <p class="hint">Значения считываются с Arduino. Примените изменения и проверьте заезд перед записью в EEPROM.</p>
  <div class="robot-form-grid">${lineFields.map(({key,label,min,max})=>`
   <div class="form-row"><label for="live-${key}">${label}</label><input id="live-${key}" type="number" min="${min}" max="${max}" step="1"></div>`).join('')}
  </div>
  <div class="cal-buttons">
   <button id="lineApply" class="primary">Применить</button><button id="lineSave" data-command="line save">Сохранить в EEPROM</button>
   <button id="lineClear">Вернуть параметры из прошивки</button>
  </div>
  <p class="hint" id="lineFeedback" role="status"></p>
 `;
 const groups=document.createElement('div');
 groups.className='robot-groups';
 const cards=[
  section('Проба моторов',real), section('Сервопривод',limits,true),
  section('Скорости моторов',motor,true), section('Движение по линии',tuning), section('Датчики',sensors),
  section('Звуковые сигналы',sound), section('Прошивка',flashing),
  section('Терминал COM',terminal)
 ];
 groups.append(...cards);
 const shortcuts=document.createElement('nav');
 shortcuts.className='robot-shortcuts';
 shortcuts.setAttribute('aria-label','Узлы робота');
 for(const card of cards){
  const button=document.createElement('button');
  button.textContent=card.querySelector('summary').textContent;
  button.onclick=()=>{
   card.open=true;
   card.querySelector('summary').focus({preventScroll:true});
   card.scrollIntoView({block:'start'});
  };
  button.setAttribute('aria-label','Открыть раздел «'+button.textContent+'»');
  shortcuts.append(button);
 }
 pane.replaceChildren(connectionBar,$('serialSupport'),dashboard,shortcuts,groups);
 const idleStates=[0,16,17];
 const states=['Ожидание','Поворот к лучу','Выезд из круга','Поиск линии','Поиск груза','Подъезд к грузу','Подъём вил','Отход','Разворот','Возврат в круг','Подъезд к центру','Переезд','К месту выгрузки','Подъезд к выгрузке','Опускание вил','Отъезд после выгрузки','Готово','Остановка','По линии до груза'];
 const faults=['','Ошибка настроек','Груз не найден','Линия потеряна','Зона не найдена','Круг не найден','Линия после разворота не найдена','Не удалось выехать на линию','Груз потерян','Груз застрял','Остановлено','Лимит времени заезда','Подъёмник не успел переместиться','Линия при развороте найдена слишком рано'];
 const modeHelp=()=>$('robotModeHelp').textContent=$('robotMode').value==='line'
  ?'Поставьте робота на линию с опущенными вилами. У груза он остановится и поднимет его. Для этого режима достаточно калибровки белого и чёрного.'
  :'Поставьте робота в заданный стартовый круг. Он ищет груз по лучам и отвозит его в зону разгрузки.';
 modeHelp();
 let telemetry=null,limitsLoaded=false,motorDirty=false,dynamicsDirty=false,lineDirty=false;
 let busy=false,controller=null,monitor=null,openingMonitor=false;
 const telemetryPlaceholders=Object.fromEntries(
  ['liveHardware','servoLimitsStatus','servoDirectionStatus','motorConfigStatus'].map(id=>[id,$(id).textContent])
 );
 function showStage(state,fault,held,armed=false){
  $('robotStage').textContent=armed&&state===0?'Запуск разрешён':faults[fault]||states[state]||'—';
  if(held)$('robotCargo').textContent='Поднят';
  if(state===16||state===17)$('robotWheels').textContent='0 / 0';
 }
 const log=s=>{$('serialLog').textContent=($('serialLog').textContent+'\n'+s).slice(-10000);$('serialLog').scrollTop=$('serialLog').scrollHeight;const status=String(s).match(/angle=(\d+).*?servo_output=(\d+).*?servo_goal=(\d+).*?servo_low=(\d+).*?servo_high=(\d+).*?start_button=(\d).*?raw=([^=]+?) line=.*?contact=(\d)/);
 if(status){
  const [angle,physical,goal,low,high,start,raw,contact]=status.slice(1);
  const settled=String(s).match(/servo_settled=(0|1)/);
  const state=Number(s.match(/^state=(\d+)/)?.[1]);
  const fault=Number(s.match(/\bfault=(\d+)/)?.[1]);
  const mode=s.match(/\bmode=(0|1)/)?.[1];
  const armed=s.match(/\barmed=(0|1)/)?.[1]==='1';
  telemetry={angle:Number(angle),goal:Number(goal),settled:settled?.[1]==='1',state,armed,mode};
  $('robotCargo').textContent=contact==='1'?'Обнаружен':'Нет';
  showStage(state,fault,s.includes(' held=1 '),armed);
  if(mode===undefined)$('robotFeedback').textContent='Выбор режима доступен после обновления прошивки.';
  else if($('robotFeedback').textContent==='Ожидание ответа Arduino…')$('robotFeedback').textContent='Выберите режим и разрешите запуск.';
  $('robotLift').textContent=angle===goal?angle+'°':angle+'° → '+goal+'°';
  if(mode!==undefined){$('robotMode').value=mode==='1'?'line':'full';modeHelp();}
  const polarity=s.match(/\bcontact_low=(0|1)/)?.[1],pullup=s.match(/\bcontact_pullup=(0|1)/)?.[1];
  if(polarity!==undefined)$('cargoActiveLevel').value=polarity==='1'?'low':'high';
  if(pullup!==undefined)$('cargoPullup').value=pullup==='1'?'on':'off';
  const diag=String(s).match(/pwm=(-?\d+)\s+(-?\d+)\s+target=(-?\d+)\s+(-?\d+)\s+err=(-?\d+)\s+corr=(-?\d+)\s+dfilter=(-?\d+)\s+lost_ms=(\d+).*?\bcal=(\d+)/);
  const applied=String(s).match(/motor_applied=(-?\d+),(-?\d+)\s+motor_jog=(0|1)/);
  $('robotWheels').textContent=applied?applied[1]+' / '+applied[2]:diag?diag[1]+' / '+diag[2]:'—';
  const motorFeedback=applied?` · на драйвере ${applied[1]}/${applied[2]}${applied[3]==='1'?' (проба)':''}`:'';
  const navigation=diag?` · PWM ${diag[1]}/${diag[2]} (цель ${diag[3]}/${diag[4]}) · ошибка ${diag[5]} · коррекция ${diag[6]} · потеря ${diag[8]} мс · калибровка ${diag[9]==='0'?'готова':diag[9]==='1'?'неполная':'круги неразличимы'}`:'';
  $('liveHardware').textContent=`Серво: команда ${angle}° → ${goal}° · выход D9: ${physical}° · ${telemetry.settled?'программная выдержка завершена':'перемещение / выдержка'} · датчики ${raw.trim()} · старт ${start==='1'?'нажата':'отпущена'} · груз ${contact==='1'?'есть':'нет'}${navigation}${motorFeedback}`;
  $('servoLimitsStatus').textContent=`В Arduino сохранены рабочие положения ${low}° и ${high}°.`;
  if(!limitsLoaded||String(s).includes('SERVO LIMITS SAVED')){
   $('servoLow').value=low;$('servoHigh').value=high;$('servoTarget').value=goal;
   limitsLoaded=true;
  }
  const values=s.match(/\bline_tuning=([\d,]+)/)?.[1].split(',');
  if(values?.length===lineFields.length&&!lineDirty)lineFields.forEach(({key},i)=>{$('live-'+key).value=values[i];});
  buttons();
 }
 if(s.startsWith('m=')||s.startsWith('motion=')){
  const legacy=s.startsWith('motion=');
  const values=s.slice(legacy?7:2).split(',').map(field=>field.trim()===''?NaN:Number(field));
  if(values.length===(legacy?12:14)&&values.every(Number.isInteger)){
   recordDiagnostic('sample',legacy?[...values,'','']:values);
   const [state,fault,left,centre,right,pwmL,pwmR,angle,contact,held,error,marker]=values;
   if(telemetry)telemetry.state=state;
   $('robotCargo').textContent=contact?'Обнаружен':'Нет';
   $('robotLift').textContent=angle+'°';
   $('robotWheels').textContent=pwmL+' / '+pwmR;
   showStage(state,fault,held,telemetry?.armed);
   $('liveHardware').textContent=`Датчики ${left} / ${centre} / ${right} · на драйвере ${pwmL}/${pwmR} · ошибка линии ${error} · отметка ${marker?'да':'нет'}`;
   buttons();
  }
 }
 const transition=s.match(/^stage=(\d+) fault=(\d+) held=(0|1)$/);
 if(transition){
  const row=Array(14).fill('');
  row[0]=transition[1];row[1]=transition[2];row[9]=transition[3];
  recordDiagnostic('stage',row);
  const state=Number(transition[1]);
  if(telemetry){telemetry.state=state;telemetry.armed=false;}
  showStage(state,Number(transition[2]),transition[3]==='1');
  if(state===16)$('robotFeedback').textContent=transition[3]==='1'?'Груз поднят. Снимите груз, опустите вилы и выполните сброс.':'Заезд завершён.';
  else if(state===17)$('robotFeedback').textContent='Робот остановлен. Причина указана в поле «Этап».';
  else if(state===0)$('robotFeedback').textContent='Робот готов. Разрешите запуск для следующего заезда.';
  else $('robotFeedback').textContent='Робот выполняет заезд.';
  buttons();
 }
 if(s==='LINE UPDATED'){lineDirty=false;buttons();$('lineFeedback').textContent='Применено до перезагрузки. Для постоянной записи нажмите «Сохранить в EEPROM».';}
 if(s==='LINE SAVED')$('lineFeedback').textContent='Сохранено в EEPROM.';
 if(s==='LINE CLEARED')$('lineFeedback').textContent='Переопределения удалены. Перезапустите Arduino.';
 if(s.startsWith('LINE REFUSED'))$('lineFeedback').textContent='Проверьте диапазоны. Порог линии должен быть ниже порога широкой отметки.';
 if(String(s).startsWith('SERVO REFUSED')||String(s).startsWith('BUSY')||String(s).startsWith('RESET REQUIRED'))$('servoLimitsStatus').textContent=s;
 if(/^(START REFUSED|LOWER FORKS|CONTACT ALREADY|STOPPED|ARMED|CAL REQUIRED|CAL HUB OVERLAP|RESET REFUSED|BUSY|UNKNOWN COMMAND)/.test(s)){
  const messages={
   'LOWER FORKS':'Перед стартом опустите вилы и дождитесь остановки сервопривода.',
   'CONTACT ALREADY':'Датчик уже видит груз. Освободите вилы перед запуском.',
   'CAL REQUIRED':'Сначала откалибруйте датчики в разделе «Датчики».',
   'CAL HUB OVERLAP':'Заново откалибруйте левый и правый круги.',
   'START REFUSED':'Для старта нужен сброс, разрешение запуска и отпущенная кнопка START.',
   'RESET REFUSED':'Для сброса опустите вилы и снимите груз.',
   'STOPPED':'Робот остановлен. Перед новым заездом сбросьте состояние.',
   'ARMED':'Запуск разрешён.',
   'BUSY':'Робот выполняет команду. Дождитесь окончания или нажмите «Стоп».',
   'UNKNOWN COMMAND':'Эта команда требует обновления прошивки.'
  };
  $('robotFeedback').textContent=messages[Object.keys(messages).find(key=>s.startsWith(key))];
 }
 if(s.startsWith('CAL HUB OVERLAP'))$('calibrationFeedback').textContent='Показания кругов перекрываются. Снимите образцы левого и правого кругов заново.';
 if(s.startsWith('CAL REQUIRED'))$('calibrationFeedback').textContent='Снимите образцы белого, чёрного и требуемых кругов.';
 if(s.startsWith('CAL SAMPLE OK')||s==='EEPROM SAVED')$('calibrationFeedback').textContent=s==='EEPROM SAVED'?'Калибровка сохранена.':'Образец записан. После завершения нажмите «Сохранить».';
 if(String(s)==='SERVO LIMITS SAVED'){limitsLoaded=false;$('servoLimitsStatus').textContent='Положения записаны в Arduino.';}
 const mt=String(s).match(/motor_min=(\d+),(\d+)\s+motor_trim=(\d+),(\d+)\s+motor_speed=(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\s+motor_ramp=(\d+),(\d+)/);
 if(mt){
  if(!motorDirty)motorDefs.forEach(([id],i)=>{$(id).value=mt[i+1];});
 }
 const dynamics=String(s).match(/\bmotor_dynamics=(\d+),(\d+)/);
 if(dynamics&&!dynamicsDirty)dynamicsDefs.forEach(([id],i)=>{$(id).value=dynamics[i+1];});
 if(s.startsWith('MOTOR DYNAMICS UPDATED')){dynamicsDirty=false;$('motorConfigStatus').textContent='Пусковой толчок применён. Сохраните всё в EEPROM.';}
 if(s.startsWith('MOTOR UPDATED')){motorDirty=false;$('motorConfigStatus').textContent='Применено в RAM; не сохранено в EEPROM.';}
 if(s.startsWith('MOTOR SAVED'))$('motorConfigStatus').textContent='Сохранено в EEPROM.';
 if(s.startsWith('MOTOR CLEARED'))$('motorConfigStatus').textContent='EEPROM очищена. Перезапустите плату для возврата к настройкам прошивки.';
  if(s.startsWith('JOG KICK START'))$('realProbeStatus').textContent='Пусковой импульс подан. '+s;
  if(s.startsWith('JOG HOLD'))$('realProbeStatus').textContent='Удержание рабочего PWM без пауз: '+s.replace('JOG HOLD ','');
  if(s.startsWith('JOG DONE'))$('realProbeStatus').textContent='Проба завершена. Продолжал ли мотор вращаться на низком PWM?';
  if(s.startsWith('JOG REFUSED'))$('realProbeStatus').textContent=s;
 if(s.startsWith('MOTOR REFUSED')||s==='UNKNOWN COMMAND')$('motorConfigStatus').textContent=s==='UNKNOWN COMMAND'?'Обновите прошивку: команда не поддерживается.':s;
 if(s.startsWith('RADIAL READY')){
  if(monitor)clearTimeout(monitor.statusTimer);
  send('status').catch(e=>log(e.message));
 }
 const match=String(s).match(/(?:servo_reverse|SERVO SAVED reverse)=(0|1)/);if(match){if(String(s).startsWith('SERVO SAVED')){limitsLoaded=false;}$('servoDirection').value=match[1]==='1'?'reverse':'normal';$('servoDirectionStatus').textContent='Плата сообщает: '+(match[1]==='1'?'обратное':'обычное')+' направление SG90. Сохранено в EEPROM. Установите качалку в нижнем положении при выключенном питании.';}};
 const supported=!!navigator.serial&&isSecureContext;
 $('serialSupport').textContent=supported?'Подключите Arduino по USB и выберите её COM-порт в окне браузера.':('USB здесь недоступен. Откройте файл в Chrome или Edge. Если не помогло — попросите наставника открыть страницу через HTTPS или localhost.');
 function syncBoard(){const raw=getCfg().uploadBoard,key=typeof raw==='string'&&AmurFlash.profiles[raw]?raw:'uno';getCfg().uploadBoard=key;$('boardProfile').value=key;$('boardHelp').textContent=key.startsWith('nano')?'У китайской Nano могут быть разные загрузчики. Не знаете — выберите автоподбор. CH340 не указывает тип загрузчика.':'Обычная UNO: 115200. Для неизвестного загрузчика выберите автоподбор. Происхождение платы и USB-чип не определяют загрузчик; поддерживается ATmega328P, 16 МГц.';} $('boardProfile').onchange=()=>{getCfg().uploadBoard=$('boardProfile').value;syncBoard();};syncBoard();
 function buttons(){
  const connected=!!monitor&&!monitor.closing;
  const locked=busy||openingMonitor||!!monitor;
  // The monitor owns the port, but flashing may safely close it first.
  $('flashUno').disabled=!supported||busy||openingMonitor||!!monitor?.closing;
  $('openMonitor').disabled=!supported||locked;
  $('closeMonitor').disabled=!connected;
  $('cancelFlash').disabled=!controller;
  $('downloadHex').disabled=busy;
  $('boardProfile').disabled=$('manualReset').disabled=locked;
  $('applyServoDirection').disabled=!connected||!$('servoDetached').checked;
  for(const id of ['motorApply','motorDynamicsApply','motorSave','motorClear'])$(id).disabled=!connected;
  $('portStatus').textContent=connected?'COM подключён · 115200 бод':openingMonitor?'Подключение…':busy?'Запись прошивки':'COM отключён';
  for(const button of pane.querySelectorAll('[data-command],[data-real-command],[data-real-jog],#calButtons button,#serialForm button'))button.disabled=!connected;
  const currentMode=connected&&telemetry?.mode!==undefined;
  const stopped=idleStates.includes(telemetry?.state);
  $('robotMode').disabled=!currentMode||!stopped;
  if(currentMode&&!stopped)$('flashUno').disabled=true;
  $('armMission').disabled=!currentMode||telemetry.state!==0||telemetry.armed;
  $('startMission').disabled=!currentMode||telemetry.state!==0||!telemetry.armed;
  $('cargoActiveLevel').disabled=$('cargoPullup').disabled=!connected;
  for(const id of ['lineApply','lineSave','lineClear'])$(id).disabled=!currentMode||!stopped;
  if(lineDirty)$('lineSave').disabled=true;
  for(const id of ['servoBack','servoForward','servoPreview'])$(id).disabled=!connected||!telemetry;
  for(const id of ['captureLow','captureHigh','saveServoLimits'])$(id).disabled=!connected||!telemetry?.settled;
 }
 function image(){if(configError())throw Error('Сначала исправьте настройки программы');return AmurFlash.patch(base,AmurFlash.boardMeta(meta,getCfg().uploadBoard||'uno'),getCfg());}
 $('downloadHex').onclick=()=>{try{download((getCfg().uploadBoard||'uno').startsWith('nano')?'Pogruzchik_NANO.hex':'Pogruzchik_UNO.hex',AmurFlash.hex(image()));log('HEX сформирован с текущими настройками.');}catch(e){log(e.message);}};
 $('flashUno').onclick=async()=>{
  if(busy||openingMonitor||monitor?.closing)return;
  busy=true;flashFeedback.textContent='Подготовка к записи…';buttons();
  try{
   // A connected monitor is not an error: close it and release its locks
   // before opening the bootloader on the same COM port.
   if(monitor){
    log('Освобождаю COM-порт: отключаю монитор перед прошивкой.');
    await $('closeMonitor').onclick();
    if(monitor)throw Error('Монитор COM-порта ещё не отключился. Повторите попытку.');
   }
   const firmware=image(),key=getCfg().uploadBoard||'uno';
   const port=await navigator.serial.requestPort();
   controller=new AbortController();buttons();
   await AmurFlash.uploadBoard(port,firmware,meta,key,(p,s)=>{$('flashProgress').value=p;flashFeedback.textContent=s;log(s);},controller.signal,$('manualReset').checked);
  }catch(e){
   flashFeedback.textContent=e.name==='NotFoundError'?'Порт не выбран. В окне браузера нажмите на свою плату / COM-порт, затем «Подключить».':e.name==='NetworkError'?'Не удалось открыть порт. Закройте Arduino IDE и другие вкладки с подключением к плате.':'Загрузка: '+e.message;
   log(flashFeedback.textContent);
  }finally{busy=false;controller=null;buttons();}
 };
 $('cancelFlash').onclick=()=>controller?.abort();
 function clearTelemetry(){
  telemetry=null;limitsLoaded=false;motorDirty=false;dynamicsDirty=false;lineDirty=false;
  for(const [id,message] of Object.entries(telemetryPlaceholders))$(id).textContent=message;
  for(const id of ['servoLow','servoHigh','servoTarget'])$(id).value='';
  $('calibrationFeedback').textContent=$('lineFeedback').textContent='';
  for(const {key} of lineFields)$('live-'+key).value='';
  $('servoDetached').checked=false;
  $('servoDirection').value='normal';
  for(const id of ['robotStage','robotCargo','robotLift','robotWheels'])$(id).textContent='—';
  $('robotFeedback').textContent='Подключите Arduino, чтобы управлять роботом.';
 }
 async function releaseMonitor(session){
  session.closing=true;clearTimeout(session.statusTimer);clearTelemetry();buttons();
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
   $('robotFeedback').textContent='Ожидание ответа Arduino…';
   session.statusTimer=setTimeout(()=>send('status').catch(e=>log(e.message)),1400);
  }catch(e){
   const message=e.name==='NotFoundError'?'COM-порт не выбран.':'Не удалось подключиться: '+e.message;
   log(message);
   $('robotFeedback').textContent=message;
  }
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
 
 motorDefs.forEach(([id])=>$(id).addEventListener('input',()=>{motorDirty=true;}));
 dynamicsDefs.forEach(([id])=>$(id).addEventListener('input',()=>{dynamicsDirty=true;}));
 $('motorApply').onclick=()=>{
  const values=motorDefs.map(([id])=>$(id).value===''?NaN:Number($(id).value));
  if(values.some((v,i)=>!Number.isInteger(v)||v<motorDefs[i][2]||v>motorDefs[i][3])){
   $('motorConfigStatus').textContent='Проверьте диапазоны и целые значения всех параметров.';return;
  }
  send('motor set '+values.join(' ')).catch(e=>log(e.message));
 };
 $('motorDynamicsApply').onclick=()=>{
  const values=dynamicsDefs.map(([id])=>$(id).value===''?NaN:Number($(id).value));
  if(values.some((v,i)=>!Number.isInteger(v)||v<dynamicsDefs[i][2]||v>dynamicsDefs[i][3])){
   $('motorConfigStatus').textContent='Допустимы PWM 0–255 и длительность 0–150 мс.';return;
  }
  send('motor dynamics '+values.join(' ')+' 0 110 160 16').catch(e=>log(e.message));
 };
 for(const {key} of lineFields)$('live-'+key).addEventListener('input',()=>{lineDirty=true;buttons();});
 $('lineApply').onclick=()=>{
  const values=lineFields.map(({key})=>$('live-'+key).valueAsNumber);
  if(values.some((n,i)=>!Number.isInteger(n)||n<lineFields[i].min||n>lineFields[i].max)){
   $('lineFeedback').textContent='Заполните все поля целыми числами в допустимых диапазонах.';
   return;
  }
  command('line set '+values.join(' '));
 };
 $('lineClear').onclick=()=>{
  if(confirm('Удалить сохранённые параметры линии? Значения из прошивки вступят в силу после перезапуска Arduino.'))command('line clear');
 };
 $('motorSave').onclick=()=>send('motor save').catch(e=>log(e.message));
 $('motorClear').onclick=()=>{if(confirm('Очистить EEPROM настроек моторов? Настройки прошивки вернутся после перезапуска Arduino.'))send('motor clear').catch(e=>log(e.message));};
 $('servoDetached').onchange=buttons;$('applyServoDirection').onclick=()=>{if(!monitor||monitor.closing||!$('servoDetached').checked)return;const mode=$('servoDirection').value;if(!['normal','reverse'].includes(mode))return;send('servo '+mode+' detached').catch(e=>log(e.message));$('servoDetached').checked=false;buttons();};
 for(const [label,command]of [['Разрешить пробы','arm'],['↑ Поднять вилы','high'],['↓ Опустить вилы','low'],['Сброс','reset'],['■ Стоп','stop']]){const b=document.createElement('button');b.textContent=label;b.dataset.realCommand=command;b.onclick=()=>send(command).catch(e=>log(e.message));$('realControls').append(b);}
 for(const [label,l,r]of [['↑ Вперёд',1,1],['↓ Назад',-1,-1],['↶ Влево',-1,1],['↷ Вправо',1,-1],['Только левый',1,0],['Только правый',0,1]]){
   const button=document.createElement('button');button.textContent=label;button.dataset.realJog=l+','+r;
   button.onclick=()=>{
    const lp=$('realLeftPwm').value===''?NaN:Number($('realLeftPwm').value);
    const rp=$('realRightPwm').value===''?NaN:Number($('realRightPwm').value);
    const t=$('realDuration').value===''?NaN:Number($('realDuration').value);
    if(!Number.isInteger(lp)||lp<0||lp>255||!Number.isInteger(rp)||rp<0||rp>255||
       !Number.isInteger(t)||t<50||t>2000||(l*lp===0&&r*rp===0)){
     $('realProbeStatus').textContent='PWM 0–255; время 50–2000 мс; хотя бы одно колесо должно двигаться.';return;
    }
    const kick=$('realUseKick').checked,kp=$('realKickPwm').value===''?NaN:Number($('realKickPwm').value),km=$('realKickMs').value===''?NaN:Number($('realKickMs').value);
    if(kick&&(!Number.isInteger(kp)||kp<1||kp>255||!Number.isInteger(km)||km<1||km>150||km>=t)){
     $('realProbeStatus').textContent='PWM толчка 1–255; длительность 1–150 мс и обязательно короче всей пробы.';return;
    }
    const command=(kick?'jogkick ':'jog ')+(l*lp)+' '+(r*rp)+' '+t+(kick?' '+kp+' '+km:'');
    $('realProbeStatus').textContent=kick?'Проверяйте движение после пускового толчка: '+km+' мс пуска, '+(t-km)+' мс удержания.':'Обычная проба без пускового толчка.';
    send(command).catch(e=>log(e.message));
   };
   $('realControls').append(button);
  }
 const command=s=>{
  if(s==='arm'&&telemetry?.mode!==undefined){send('arm').then(()=>send('status')).catch(e=>log(e.message));return;}
  if(s==='reset'&&telemetry?.mode!==undefined){send('reset').then(()=>send('status')).catch(e=>log(e.message));return;}
  if(s==='start'){
   telemetry.armed=false;
   buttons();
   $('robotFeedback').textContent='Команда запуска отправлена.';
  }

  if(telemetry && /^(angle |low$|high$|stop$)/.test(s)){telemetry.angle=null;telemetry.settled=false;buttons();}
  send(s).catch(e=>log(e.message));
 };
 $('robotMode').onchange=()=>{
  modeHelp();
  $('robotFeedback').textContent='Режим сохранится в Arduino. Разрешите запуск перед заездом.';
  telemetry.armed=false;
  buttons();
  command('mode '+$('robotMode').value);
 };
 $('cargoActiveLevel').onchange=()=>command('contact '+$('cargoActiveLevel').value);
 $('cargoPullup').onchange=()=>command('contact pullup '+$('cargoPullup').value);
 for(const button of pane.querySelectorAll('[data-command]'))button.onclick=()=>command(button.dataset.command);
 const angle=id=>$(id).value===''?NaN:Number($(id).value);
 const preview=value=>{
  if(Number.isInteger(value)&&value>=0&&value<=180){$('servoTarget').value=value;telemetry.goal=value;command('angle '+value);}
  else $('servoLimitsStatus').textContent='Укажите целый угол от 0 до 180°.';
 };
 $('servoPreview').onclick=()=>preview(angle('servoTarget'));
 $('servoBack').onclick=()=>preview(telemetry.goal-1);
 $('servoForward').onclick=()=>preview(telemetry.goal+1);
 for(const [button,input] of [['captureLow','servoLow'],['captureHigh','servoHigh']]){
  $(button).onclick=()=>{
   if(telemetry.angle===null||telemetry.angle!==telemetry.goal||!telemetry.settled){$('servoLimitsStatus').textContent='Дождитесь окончания программной выдержки и нажми «Статус» или включи телеметрию. Положение вала проверь визуально.';return;}
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
