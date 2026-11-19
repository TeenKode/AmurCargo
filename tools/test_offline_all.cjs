// End-to-end offline check for the generated one-file navigation.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium,browserExecutable}=require('./runtime_paths.cjs');
(async()=>{
  const file=path.resolve('OFFLINE.html');
  assert(fs.existsSync(file),'Generate OFFLINE.html first');
  const browser=await chromium.launch({executablePath:browserExecutable,headless:true,args:['--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1280,height:860}});
  const errors=[],external=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',req=>{if(/^https?:/i.test(req.url()))external.push(req.url());});
  try{
    await page.goto('file://'+file);
    assert(await page.locator('#home').isVisible());
    await page.locator('nav [data-section=quick]').click();
    const quick=page.frameLocator('iframe[title="Как начать"]');
    assert((await quick.locator('body').textContent()).includes('Открой симулятор'));
    await page.locator('nav [data-section=calibration]').click();
    assert.equal(await page.frameLocator('iframe[title="Калибровка"]').locator('h2').count(),8);
    await page.locator('nav [data-section=purchase]').click();
    assert(await page.frameLocator('iframe[title="Список покупок"]').locator('table').count()>0);
    await page.locator('nav [data-section=assembly]').click();
    const assembly=page.frameLocator('iframe[title="Сборка и подключение"]');
    await assembly.locator('figure img').first().waitFor();
    assert.equal(await assembly.locator('figure img').count(),7);
    await page.locator('nav [data-section=sim]').click();
    await page.waitForFunction(()=>document.querySelector('iframe[title="3D-симулятор"]')?.contentWindow?.radialTest?.ready,{timeout:60000});
    assert(await page.frameLocator('iframe[title="3D-симулятор"]').locator('[data-tab=arduino]').count()>0);
    const frame=await page.locator('iframe[title="3D-симулятор"]').elementHandle();
    await page.locator('nav [data-section=quick]').click();
    await page.locator('nav [data-section=sim]').click();
    assert(await page.locator('iframe[title="3D-симулятор"]').elementHandle()!==null);
    const reused=await page.evaluate(()=>document.querySelectorAll('iframe[title="3D-симулятор"]').length);
    assert.equal(reused,1,'Simulator should not reload when switching sections');
    assert.deepEqual(errors,[],'Page errors: '+errors.join(', '));
    assert.deepEqual(external,[],'External requests: '+external.join(', '));
    await page.setViewportSize({width:390,height:844});
    assert(await page.locator('nav [data-section=sim]').isVisible());
    console.log('PASS unified offline HTML: navigation, all sections, 3D runtime, offline assets, mobile');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
