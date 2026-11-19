from pathlib import Path
import base64
R=Path(__file__).resolve().parents[1]; O=R/'simulator'
p=O/'simulation.js'
s=p.read_text(encoding='utf-8').replace('this.trace.push({x:this.robot.x,y:this.robot.y})','this.trace.push({x:this.robot.x,y:this.robot.y,loaded:this.cargo.attached})')
t=(R/'tools/radial_simulator.html').read_text(encoding='utf-8')
t=t.replace('!Number.isInteger(n/step)','Math.abs(n/step-Math.round(n/step))>1e-6')
t=t.replace('r<250||r>750))))','r<250||r>750)))')
t=t.replace("const p=n.physics;if(!p", "if(n.cargoRay===(n.values[0]?4:0))throw Error('Груз должен находиться в погрузочной зоне');const p=n.physics;if(!p")
t=t.replace('__PHYSICS__',s).replace('__SCHEMA__',(O/'settings_schema.json').read_text(encoding='utf-8')).replace('__WASM__',base64.b64encode((R/'firmware/build/FirmwareCore.wasm').read_bytes()).decode())
(O/'Open_Simulation.html').write_text(t,encoding='utf-8')
print('Self-contained simulation:',len(t),'characters')
