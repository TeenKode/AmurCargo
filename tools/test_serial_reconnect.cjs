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
  await page.evaluate(()=>{
   window.ports=[];
   Object.defineProperty(window,'isSecureContext',{value:true});
   Object.defineProperty(navigator,'serial',{value:{async requestPort(){
    const port={
     async open(){
      this.readable=new ReadableStream({start:controller=>{this.input=controller;}});
      this.writable=new WritableStream();
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
   setupAmurSerial({getCfg:()=>config});
  });
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
  assert.deepEqual(errors,[]);
  console.log('PASS Serial monitor releases locks and clears telemetry on EOF, read error and manual close');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
