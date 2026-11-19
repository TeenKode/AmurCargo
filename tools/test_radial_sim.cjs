const fs=require('fs'),path=require('path'),{Simulation,defaults,names}=require('../simulator/simulation.js');
(async()=>{
 const folder=path.resolve('simulator'),schema=JSON.parse(fs.readFileSync(path.join(folder,'settings_schema.json'))),wasm=fs.readFileSync('firmware/build/FirmwareCore.wasm');
 const cfg=defaults(schema);const {instance}=await WebAssembly.instantiate(wasm,{});const sim=new Simulation(instance.exports,schema,cfg);console.log('bytes',instance.exports.settings_size(),instance.exports.engine_size(),'error',sim.configError);sim.start();
 let last=-1;for(let i=0;i<60000&&sim.running;i++){sim.tick();const s=sim.w.get_state();if(s!==last){console.log((sim.time/1000).toFixed(2),names[s],'hub',sim.w.get_hub(),'ray',sim.w.get_ray(),'xy',sim.robot.x.toFixed(1),sim.robot.y.toFixed(1),'angle',((sim.robot.a*180/Math.PI)%360).toFixed(1),'contact',sim.contact,'cargo',sim.cargo.attached,'read',sim.readings);last=s;}}
 console.log('END',sim.w.get_state(),sim.w.get_fault(),sim.success(),sim.cargo);
 fs.writeFileSync(path.join(folder,'debug_simulation.json'),JSON.stringify({time:sim.time,state:sim.w.get_state(),fault:sim.w.get_fault(),success:sim.success(),robot:sim.robot,cargo:sim.cargo,events:sim.events},null,2));
})().catch(e=>{console.error(e);process.exit(1);});
