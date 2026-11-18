from pathlib import Path
import json,zipfile,hashlib,html,re,posixpath
R=Path(__file__).resolve().parents[1];O=R/'simulator';P=R/'mechanics/Print_Ready'
files={};parts=[]
def add(name,path):files[name]=Path(path).read_bytes()
add('Simulator.html',O/'Open_Simulation_3D.html');add('Shopping_List.html',O/'Purchase_List_RU.html')
for p in json.loads((P/'PRINT_MANIFEST.json').read_text(encoding='utf-8')):
 if p['file'] in ('01_Fork_Pair_TipStops.stl','05_Crank_R18_Trial.stl'):continue
 add('Print/'+p['file'],P/p['file']);parts.append([p['file'],p['title'],p['quantity'],p['orientation'],p['supports']])
for name,title in [('00_Fit_Coupon.stl','Пробник отверстий и гаек'),('00_Guide_Rail.stl','Пробник направляющей'),('00_Guide_Slider.stl','Пробник ползуна')]:
 add('Print/'+name,P/name);parts.append([name,title,1,'Уже повёрнут для печати.','Сначала проверьте посадку.'])
for stem,title,quantity in [('00_M3_Plastic_Fit_Coupon','Пробник винтов в пластике',1),('01_Removable_Fork_Spine','Облегчённая спинка, плоская сзади',1),('02_Fork_Arm_Left','Левая лапа, боковой крепёж М3×16',1),('02_Fork_Arm_Right','Правая лапа, боковой крепёж М3×16',1),('03_Cargo_Button_Spacer','Проставка кнопки, 1,4 мм',2)]:
 name=stem+'.stl';add('Print/'+name,(R/'mechanics')/'Fork_Adapters'/(stem+'_Print_Orientation.stl'));parts.append([name,title,quantity,'Уже повёрнут для печати.','Спинка задней плоскостью на столе, без поддержек.' if stem.startswith('01_') else 'Поддержки обычно не нужны; отверстия очистите.'])
for filename,title in [('00_SG90_Spline_Fit_Test.stl','Пробник четырёх посадок SG90'),('SG90_Integrated_R18_21T_Fit1.stl','Цельная качалка, посадка 1'),('SG90_Integrated_R18_21T_Fit2.stl','Цельная качалка, посадка 2'),('SG90_Integrated_R18_20T_Fit3.stl','Цельная качалка, посадка 3'),('SG90_Integrated_R18_20T_Fit4.stl','Цельная качалка, посадка 4')]:
 add('Print/'+filename,(R/'mechanics')/'Servo_Horn'/filename);parts.append([filename,title,1 if filename.startswith('00_') else 'Одну подходящую','Гнездо вала вверх; уже повёрнуто.','Сначала пробник. Слой 0,08–0,12 мм; желательно сопло 0,25 мм. Не ставить поддержки в шлицы.'])
rows=''.join('<tr><td><a href="'+html.escape(n)+'">'+html.escape(title)+'</a><br><small>'+html.escape(n)+'</small></td><td>'+str(q)+'</td><td>'+html.escape(ori)+'</td><td>'+html.escape(sup)+'</td></tr>' for n,title,q,ori,sup in parts)
listing='<details id="print-files"><summary>Какие STL печатать</summary><p>Миллиметры, масштаб 100%. PETG, 5–6 стенок, заполнение 40–60%. Сначала пробники 00_. Из четырёх качалок выберите одну по пробнику.</p><div class="table"><table><thead><tr><th>Файл / деталь</th><th>Штук</th><th>Положение</th><th>Проверка</th></tr></thead><tbody>'+rows+'</tbody></table></div></details>'
guide=(O/'Assembly_Guide_Template.html').read_text(encoding='utf-8').replace('__PRINT_LIST__',listing)
files['Print/Instructions.html']=guide.encode('utf-8')
standalone=re.sub(r'<a href="([^\"]+\.stl)">([^<]+)</a>',r'\2',guide)
(O/'Assembly_Guide_RU.html').write_text(standalone,encoding='utf-8')
start='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AmurCargo — начать</title><style>body{background:#edf3f8;color:#19364a;font:17px/1.6 "Segoe UI",sans-serif}main{max-width:800px;margin:35px auto;padding:30px;background:white;border-radius:16px}a{display:block;padding:14px;margin:12px 0;background:#f1f6fb;border-radius:9px;color:#24639b}</style><main><h1>Робот-погрузчик: готовый комплект</h1><p>Распакуйте ZIP целиком. Откройте нужный HTML в Chrome или Edge.</p><a href="Print/Instructions.html">1. Сборка и подключение с картинками</a><a href="Simulator.html">2. Симулятор, настройка и прошивка UNO / Nano</a><a href="Shopping_List.html">3. Покупки и предоставленный набор</a><p>В Print — по одному STL на деталь, в положении для печати. Прошивка находится внутри симулятора. Там можно скачать HEX или проект Arduino с текущими настройками.</p><p>Новая спинка плоская сзади; лапы крепятся сбоку четырьмя М3×16 с потайной головкой. Для платы кнопки нужны две проставки 1,4 мм. Гайка качалки вставляется со стороны серво.</p><p>Симуляцию, посадки и грузоподъёмность проверьте на настоящем роботе.</p></main></html>'''
files['START.html']=start.encode('utf-8')
seen={}
for name,data in files.items():
 assert Path(name).suffix in ('.html','.stl');sha=hashlib.sha256(data).hexdigest();assert sha not in seen,(name,seen.get(sha));seen[sha]=name
for name,data in files.items():
 if not name.endswith('.html'):continue
 for target in re.findall(r'href="([^\"]+)"',data.decode('utf-8')):
  if target.startswith(('http:','https:','#','blob:')):continue
  resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),target.split('#')[0]));assert resolved in files,(name,target)
archive=R/'outputs/AmurCargo_Ready_R4_STL_HTML.zip'
archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,data in files.items():z.writestr(name,data)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report=dict(archive=str(archive),files=len(files),stl=sum(n.endswith('.stl') for n in files),html=sum(n.endswith('.html') for n in files),bytes=archive.stat().st_size,duplicate_hashes=0,local_links_valid=True,old_forks_excluded=True,firmware_embedded_only=True,entries=list(files))
(R/'tools/Ready_Archive_Checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='entries'}))
