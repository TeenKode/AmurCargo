from pathlib import Path
import re,json,base64,struct,gzip,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/AmurCargo_Radial'
vendor=R/'work/vendor'
if (vendor/'three.min.js').exists():scripts=[(vendor/'three.min.js').read_text(encoding='utf-8'),(vendor/'OrbitControls.js').read_text(encoding='utf-8')]
else:
 source=(R/'outputs/AmurCargo_Photo/Open_Prototype.html').read_text(encoding='utf-8');scripts=re.findall(r'<script[^>]*>([\s\S]*?)</script>',source)
data=json.loads((R/'outputs/AmurCargo_Photo/assembly_data.json').read_text(encoding='utf-8'))
direct_horn=json.loads((O/'Servo_Horn_Mesh.json').read_text(encoding='utf-8'))
data['items']=[direct_horn if p['name']=='SG90_original_horn' else p for p in data['items'] if p['name']!='Crank_R18' and not p['name'].startswith('Crank_horn_M1_4x6_')]
link=json.loads((O/'Servo_Link_Meshes.json').read_text(encoding='utf-8'));replacements={'Drive_pin_nut_M3':link[0],'Drive_pin_sleeve_4x3_2x11':link[1]}
data['items']=[replacements.get(p['name'],p) for p in data['items']]
forks=json.loads((O/'Fork_Adaptation_Meshes.json').read_text(encoding='utf-8'))
data['items']=[forks[0] if p['name']=='Fork_pair' else p for p in data['items']]+forks[1:]
items=[]
for p in data['items']:
 if p['name'] in ('User_Motor_0','User_Motor.001_0'):continue
 raw=base64.b64decode(p['vertices']);v=struct.unpack('<%df'%(len(raw)//4),raw);ind=struct.unpack('<%dI'%(len(base64.b64decode(p['indices']))//4),base64.b64decode(p['indices']))
 unique={};points=[];remap=[]
 for i in range(0,len(v),3):
  key=tuple(round(x*20) for x in v[i:i+3])
  if key not in unique:unique[key]=len(points)//3;points.extend(key)
  remap.append(unique[key])
 newind=[remap[i] for i in ind];p['vertices']=base64.b64encode(struct.pack('<%dh'%len(points),*points)).decode();p['indices']=base64.b64encode(struct.pack('<%dI'%len(newind),*newind)).decode();items.append(p)
encoded=base64.b64encode(gzip.compress(json.dumps(dict(items=items),separators=(',',':')).encode(),mtime=0)).decode()
t=(O/'Open_Simulation.html').read_text(encoding='utf-8')
t=t.replace('<title>','<title>3D · ',1).replace('СИМУЛЯЦИЯ АВТОНОМНОГО РОБОТА','3D-СИМУЛЯЦИЯ АВТОНОМНОГО РОБОТА').replace('02 / АЛГОРИТМ В ДЕЙСТВИИ','03 / ВИРТУАЛЬНЫЙ ПОЛИГОН').replace('Найти. Поднять. Доставить.','Доставка в трёх измерениях.')
t=t.replace('<button id="exportTop">','<button id="wideView">Больше обзора</button><button id="exportTop">',1)
t=t.replace('<div class="section"><p class="section-title">Порядок поиска</p>', '<div class="form-row"><label for="cargoPose">Положение гантели</label><select id="cargoPose"><option value="horizontal">Лежит · 70 × 40 × 40 мм</option><option value="vertical">Стоит · 40 × 40 × 70 мм</option></select></div><div class="form-row"><label for="forkProfile">Установленный комплект вил</label><select id="forkProfile"><option value="low">Низкие · опора 6 мм, зазор 20 мм</option><option value="high">Высокие · опора 32 мм, зазор 20 мм</option></select></div><p id="forkAdvice" class="hint"></p><div class="section"><p class="section-title">Порядок поиска</p>',1)
t=t.replace('</style>', '''@media(min-width:761px){.head{height:58px;padding:0 18px}.layout{height:calc(100dvh - 58px);min-height:730px;grid-template-columns:minmax(0,1fr) 300px}main{padding:12px;gap:10px}.eyebrow,.intro{display:none}h1{font-size:19px;margin:0}.metric{padding:7px 11px}.metric strong{font-size:15px}.metric small{margin-bottom:1px}.transport{padding:9px 12px}.board{min-height:470px}.legend{font-size:9px}.notice{padding:7px 10px}.wide-layout .layout{grid-template-columns:minmax(0,1fr) 0}.wide-layout aside{visibility:hidden}.wide-layout .board{min-height:540px}}@media(max-width:760px){#wideView{display:none}.board{height:440px}.maptools{flex-wrap:wrap;right:12px}.head-actions #exportTop{display:none}} </style>''',1)
t=t.replace('Колесо — масштаб · зажатое колесо — сдвиг · нажмите зону, чтобы изменить сценарий','Левая кнопка — вращение · колесо — масштаб · зажатое колесо — сдвиг')
t=t.replace('<button id="fit">Всё поле</button>','<button id="fit">Общий вид</button><button id="topView">Сверху</button>').replace('<button id="randomCargo">','<button id="spinView">↻ Облёт</button><button id="overlayRun" class="only-fullscreen">▶ Запустить</button><button id="randomCargo">')
t=t.replace('</style>','.only-fullscreen{display:none}.board:fullscreen .only-fullscreen{display:block}.board:fullscreen .maptools{flex-wrap:wrap}.scene-hud{position:absolute;bottom:30px;left:24px;background:#ffffffeb;border:1px solid #dce4ec;padding:9px 14px;border-radius:9px;font-size:12px;pointer-events:none;display:none}.board:fullscreen .scene-hud{display:block}</style>',1)
t=t.replace('<div class="field-note">','<div class="scene-hud" id="sceneHud"></div><div class="field-note">',1)
lib='<script>'+scripts[0]+'</script><script>'+scripts[1]+'</script><script>'+(R/'work/radial_3d.js').read_text(encoding='utf-8')+'</script>'
t=t.replace('<script>',lib+'<script>',1)
t=t.replace("ctx=canvas.getContext('2d')","ctx=null")
marker=' function toast(message)'
t=t.replace(marker," const viewer=await createRadial3D(canvas,board,'"+encoded+"');\n"+marker,1)
start=t.index(' function draw(){');end=t.index(' function directionOptions',start)
t=t[:start]+''' function draw(){if(sim)viewer.render(sim,cfg);}
 function resize(){viewer.resize();draw();}new ResizeObserver(resize).observe(board);
'''+t[end:]
start=t.index(' let drag=null;');end=t.index(' function download',start)
t=t[:start]+''' viewer.setClick((x,y)=>{for(let h=0;h<2;h++)for(let r=0;r<8;r++){if(r===(h?4:0))continue;const p=sim.station(h,r);if(Math.hypot(p.x-x,p.y-y)<65){if(h===val('START_HUB'))cfg.cargoRay=r;else setVal('DROP_RAY',r);forms();reset();return;}}});
 $('fit').onclick=()=>viewer.fit();$('topView').onclick=()=>viewer.fit(true);$('followRobot').onclick=()=>viewer.focus(sim);$('spinView').onclick=()=>{$('spinView').classList.toggle('primary',viewer.spin());};$('overlayRun').onclick=()=>$('run').click();
 $('wideView').onclick=()=>{const on=document.body.classList.toggle('wide-layout');$('wideView').textContent=on?'Показать настройки':'Больше обзора';requestAnimationFrame(()=>{viewer.resize();viewer.fit();});};
 function syncCargo(){const pose=cfg.cargoOrientation||'horizontal',profile=cfg.forkProfile||'low';$('cargoPose').value=pose;$('forkProfile').value=profile;$('forkAdvice').textContent=pose==='vertical'?(profile==='high'?'Высокие вилы подхватывают верхнюю пластину. Расчётный подъём ~7,7 мм; требуется физическая смена вил.':'Для стоящей гантели переставьте лапы в верхние отверстия.'):(profile==='high'?'Для лежащей гантели установите низкие вилы.':'Между лапами — 20 мм. Снаружи — 32 мм.');}
 $('cargoPose').onchange=e=>{cfg.cargoOrientation=e.target.value;syncCargo();reset();};$('forkProfile').onchange=e=>{cfg.forkProfile=e.target.value;syncCargo();reset();};syncCargo();
'''+t[end:]
t=t.replace('function reset(){playing=false;', 'function reset(){if($(\'cargoPose\'))syncCargo();playing=false;')
t=t.replace("$('run').disabled=!!sim.configError;","$('overlayRun').textContent=$('run').textContent;$('overlayRun').disabled=!!sim.configError;$('sceneHud').textContent=names[state]+' · '+fmt(sim.time)+' · груз '+sim.cargo.z.toFixed(1)+' мм';$('run').disabled=!!sim.configError;")
t=t.replace('configHeader,view};','configHeader,view,viewer};')
(O/'Open_Simulation_3D.html').write_text(t,encoding='utf-8')
(O/'3D_Model_Checks.json').write_text(json.dumps(dict(native_parts=len(items),native_model='AmurCargo_Photo/assembly_data.json',native_model_sha256=hashlib.sha256((R/'outputs/AmurCargo_Photo/assembly_data.json').read_bytes()).hexdigest(),print_checks_sha256=hashlib.sha256((R/'outputs/AmurCargo_Photo/Printability_Checks.json').read_bytes()).hexdigest(),units='mm',vertex_quantization_mm=.05,tyres='Lightweight geometry; measured diameter 68.923 mm, width 25 mm',model_axle_y_mm=35.1785,model_wheel_base_mm=132.38,servo_horn="direct 21T Fit2; provisional spline",cargo_size_mm=[70,40,40],vertical_cargo_size_mm=[40,40,70],wasm_core_unchanged=True,embedded_model_bytes=len(encoded)),indent=2),encoding='utf-8')
print('3D HTML bytes',(O/'Open_Simulation_3D.html').stat().st_size,'parts',len(items),'model encoded bytes',len(encoded))
