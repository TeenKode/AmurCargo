const assert=require('node:assert/strict');
const {chromium,browserExecutable}=require('./runtime_paths.cjs');

(async()=>{
 const browser=await chromium.launch({executablePath:browserExecutable,headless:true});
 try{
  const page=await browser.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.setContent('<section id="pane-arduino"></section>');
  await page.addScriptTag({path:'tools/webserial_uploader.js'});
  await page.addScriptTag({path:'tools/serial_panel.js'});
  const schema=require('../simulator/settings_schema.json');
  await page.evaluate(schema=>{
   window.ports=[];
   Object.defineProperty(window,'isSecureContext',{value:true});
   Object.defineProperty(navigator,'serial',{value:{async requestPort(){
    const port={
     async open(){
      this.readable=new ReadableStream({start:controller=>{this.input=controller;}});
      this.commands=[];
      this.writable=new WritableStream({write:bytes=>{this.commands.push(new TextDecoder().decode(bytes).trim());}});
     },
     async close(){
      if(this.readable.locked||this.writable.locked)throw Error('Streams still locked');
      this.closed=true;
     },
    };
    ports.push(port);
    return port;
   }}});
   const config={};
   setupAmurSerial({getCfg:()=>config,configError:()=>0,base:new Uint8Array([1]),meta:{},schema});
  },schema);
  for(const ending of ['eof','error','manual']){
   await page.locator('#openMonitor').click();
   await page.evaluate(()=>{
    const status='angle=20 servo_reverse=0 servo_output=20 servo_goal=20 servo_low=20 servo_high=140 servo_settled=1 start_button=0 raw=500 500 500 line=0 0 0 contact=0\n';
    ports.at(-1).input.enqueue(new TextEncoder().encode(status));
   });
   await page.waitForFunction(()=>!document.querySelector('#captureLow').disabled);
   if(ending==='manual')await page.locator('#closeMonitor').click();
   else await page.evaluate(kind=>{
    const input=ports.at(-1).input;
    if(kind==='eof')input.close();
    else input.error(new Error('USB removed'));
   },ending);
   await page.waitForFunction(()=>!document.querySelector('#openMonitor').disabled);
   assert(await page.evaluate(()=>ports.at(-1).closed));
   assert(await page.locator('#captureLow').isDisabled());
   assert.equal(await page.locator('#servoLow').inputValue(),'');
   assert.match(await page.locator('#portStatus').textContent(),/отключён/);
   assert.doesNotMatch(await page.locator('#liveHardware').textContent(),/20°/);
  }
  // Regression: the flash button stays available with a connected monitor.
  // Clicking it must close and unlock the existing port BEFORE selecting a
  // bootloader port. The hardware write is stubbed; we only test USB handoff.
  await page.evaluate(()=>{
   window.flashCalls=[];
   AmurFlash.patch=()=>new Uint8Array([1]);
   AmurFlash.uploadBoard=async port=>{
    const previous=ports.at(-2);
    if(!previous.closed||previous.readable.locked||previous.writable.locked)throw Error('COM still busy');
    flashCalls.push({newPort:port===ports.at(-1),closed:previous.closed});
   };
  });
  await page.locator('#openMonitor').click();
  await page.waitForFunction(()=>document.querySelector('#portStatus').textContent.includes('подключён'));
  await page.locator('summary').filter({hasText:/^Прошивка$/}).click();
  assert(await page.locator('#flashUno').isEnabled(),'Flash must be available while the monitor is connected');
  const before=await page.evaluate(()=>ports.length);
  await page.locator('#flashUno').click();
  await page.waitForFunction(()=>window.flashCalls.length===1);
  assert.equal(await page.evaluate(()=>ports.length),before+1);
  assert.deepEqual(await page.evaluate(()=>flashCalls),[{newPort:true,closed:true}]);
  assert.match(await page.locator('#serialLog').textContent(),/Освобождаю COM-порт/);
  assert.match(await page.locator('#portStatus').textContent(),/отключён/);
  assert(await page.locator('#flashUno').isEnabled(),'Flash becomes available again after the attempt');
  await page.locator('#openMonitor').click();
  const status=async (mode,armed)=>page.evaluate(({mode,armed})=>{
   const packet=`state=0 fault=0 armed=${armed} held=0 angle=20 servo_reverse=0 servo_output=20 servo_goal=20 servo_low=20 servo_high=140 servo_settled=1 start_button=0 raw=800 200 800 line=0 1000 0 contact=0 line_tuning=350,60,25,28,250,30 mode=${mode}\n`;
   ports.at(-1).input.enqueue(new TextEncoder().encode(packet));
  },{mode,armed});
  await status(0,0);
  await page.locator('#robotMode').selectOption('line');
  await status(1,0);
  await page.locator('#armMission').click();
  await status(1,1);
  await page.locator('#startMission').click();
  await page.evaluate(()=>ports.at(-1).input.enqueue(new TextEncoder().encode('stage=18 fault=0 held=0\n')));
  await page.waitForFunction(()=>document.getElementById('robotStage').textContent==='По линии до груза');
  assert(await page.locator('#robotMode').isDisabled());
  assert(await page.locator('.robot-connection [data-command=stop]').isEnabled());
  await page.evaluate(()=>ports.at(-1).input.enqueue(new TextEncoder().encode('stage=16 fault=0 held=1\n')));
  await page.waitForFunction(()=>document.getElementById('robotCargo').textContent==='Поднят');
  await page.getByRole('button',{name:'Открыть раздел «Движение по линии»'}).click();
  await page.locator('#live-KP').fill('80');
  assert(await page.locator('#lineSave').isDisabled());
  await page.locator('#lineApply').click();
  await page.evaluate(()=>ports.at(-1).input.enqueue(new TextEncoder().encode('LINE UPDATED\n')));
  await page.locator('#lineSave').click();
  const commands=await page.evaluate(()=>ports.at(-1).commands);
  assert.deepEqual(commands.filter(cmd=>cmd!=='status'),['mode line','arm','start','line set 350 80 25 28 250 30','line save']);
  await page.locator('#closeMonitor').click();
  assert.deepEqual(errors,[]);
  console.log('PASS monitor disconnect/reconnect, plus automatic safe COM release before firmware flashing');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
