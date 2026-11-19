const fs=require('fs'),assert=require('assert'),{chromium,browserExecutable}=require('./runtime_paths.cjs');
const line=(angle,goal,low=20,high=140)=>`state=0 fault=0 armed=0 hub=0 ray=0 held=0 angle=${angle} servo_reverse=0 servo_output=${angle} servo_goal=${goal} servo_low=${low} servo_high=${high} start_button=0 raw=800 800 800 line=0 0 0 contact=0 pwm=0 0 target=0 0 err=0 corr=0 dfilter=0 lost_ms=0 cal=0\n`;
(async()=>{
 const browser=await chromium.launch({executablePath:browserExecutable,headless:true,args:['--enable-unsafe-swiftshader']});
 const p=await browser.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
 try{
  await p.setContent(fs.readFileSync('simulator/Open_Simulation_3D.html','utf8'));
  await p.waitForFunction(()=>window.radialTest?.ready);
  await p.evaluate(()=>radialTest.viewer.renderer.render=()=>{});
  await p.evaluate(()=>{
   window.usbSent=[];
   const port={
    async open(){this.readable=new ReadableStream({start(c){window.usbOutput=c;c.enqueue(new TextEncoder().encode('RADIAL READY\n'));}});this.writable=new WritableStream({write(b){window.usbSent.push(new TextDecoder().decode(b));}});},
    async close(){}
   };
   Object.defineProperty(navigator,'serial',{configurable:true,value:{requestPort:async()=>port}});
  });
  await p.locator('[data-tab=arduino]').click();
  // setContent() is not a secure origin; the hardware control is disabled by
  // default. The test supplies a mocked Web Serial port, so explicitly enable it.
  await p.evaluate(()=>document.getElementById('openMonitor').disabled=false);
  await p.locator('#openMonitor').click();
  await p.waitForFunction(()=>window.usbSent.length===1);
  assert.deepEqual(await p.evaluate(()=>window.usbSent),['status\n']);
  const sendLine=async s=>p.evaluate(s=>window.usbOutput.enqueue(new TextEncoder().encode(s)),s);
  await sendLine(line(20,20));await p.waitForFunction(()=>document.getElementById('servoTarget').value==='20');
  await p.locator('#servoTarget').fill('31');
  await p.locator('#servoPreview').click();
  await p.waitForFunction(()=>window.usbSent.includes('angle 31\n'));
  await sendLine(line(20,31));
  await p.waitForFunction(()=>document.getElementById('liveHardware').textContent.includes('20° → 31°'));
  await sendLine(line(31,31));
  await p.waitForFunction(()=>document.getElementById('liveHardware').textContent.includes('31° → 31°'));
  await p.locator('#captureLow').click();
  assert.equal(await p.locator('#servoLow').inputValue(),'31');
  await p.locator('#servoTarget').fill('119');await p.locator('#servoPreview').click();
  await p.waitForFunction(()=>window.usbSent.includes('angle 119\n'));
  await sendLine(line(31,119));await sendLine(line(119,119));
  await p.waitForFunction(()=>document.getElementById('liveHardware').textContent.includes('119° → 119°'));
  await p.locator('#captureHigh').click();
  assert.equal(await p.locator('#servoHigh').inputValue(),'119');
  await p.locator('#saveServoLimits').click();
  await p.waitForFunction(()=>window.usbSent.includes('limits 31 119\n'));
  await sendLine('SERVO LIMITS SAVED\n');
  await sendLine(line(119,119,31,119));
  await p.waitForFunction(()=>document.getElementById('servoLimitsStatus').textContent.includes('31° и 119°'));
  assert.equal(await p.locator('#servoLow').inputValue(),'31');
  assert.equal(await p.locator('#servoHigh').inputValue(),'119');
  // Reject invalid reversed limits before sending anything to Arduino.
  const sentBefore=await p.evaluate(()=>usbSent.length);
  await p.locator('#servoLow').fill('150');
  await p.locator('#servoHigh').fill('100');
  await p.locator('#saveServoLimits').click();
  assert.equal(await p.evaluate(()=>usbSent.length),sentBefore);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS: preview, completion status, low/high capture, EEPROM command, UI validation');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
