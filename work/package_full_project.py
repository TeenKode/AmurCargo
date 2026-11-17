from pathlib import Path
import json,zipfile,hashlib,re,html,ast,struct
R=Path(__file__).resolve().parents[1];O=R/'outputs/AmurCargo_Radial';P=R/'outputs/AmurCargo_Photo';M=R/'work/full_meta';M.mkdir(exist_ok=True)
readme='''# AmurCargo — робот-погрузчик

Проект для кейса КнААЗ: найти груз на одном радиальном поле, поднять его и перенести в зону второго круга.

## Начать работу

Скачайте репозиторий целиком: **Code → Download ZIP**, распакуйте и откройте `START.html`.

- [3D-симулятор](outputs/AmurCargo_Radial/Open_Simulation_3D.html) — один HTML без сетевых зависимостей.
- [Сборка и подключение с картинками](outputs/AmurCargo_Radial/Assembly_Guide_RU.html) — 10 шагов, 7 видов текущей модели и 8 схем.
- [Покупки и предоставленный набор](outputs/AmurCargo_Radial/Purchase_List_RU.html).
- [Короткий список покупок с количествами](Shopping_short.txt).
- [Исходники Arduino](outputs/AmurCargo_Radial/RadialRobot).
- [Как пересобрать проект](BUILD.md).

GitHub показывает исходный текст HTML. Для запуска откройте скачанный файл в Chrome или Edge. GitHub Pages отдельно не включён.

## Возможности

- Редактирование размеров поля на карте, выбор груза и зоны разгрузки.
- Автоматический поиск, захват и доставка; лежащая и стоящая гантель.
- Ручные проверки вил, короткие движения, замеры пути и поворота, подгонка модели по реальным результатам.
- UNO / Nano ATmega328P, загрузка через Web Serial и скачивание полного проекта Arduino с текущими настройками.
- Отдельное управление настоящим роботом по USB, калибровка датчиков и сохранение направления SG90 в EEPROM.
- Облегчённая спинка с плоской задней стороной и съёмные лапы на боковых М3×16. Цельная качалка R18: гайка приводного винта с обратной стороны; втулка 4 / 3,2 × 10,5 мм.

## Печать

Актуальные файлы перечислены в инструкции. Основные STL находятся в `outputs/AmurCargo_Photo/Print_Ready`; новые съёмные вилы — в `outputs/AmurCargo_Radial/Fork_Adapters`, качалка и пробник — в `Servo_Horn`.

Для вил берите файлы `*_Print_Orientation.stl`. Из четырёх посадок качалки печатается одна после примерки пробника. STEP в `Print_Parts` — редактируемые исходные заготовки; это не дополнительный комплект для печати.

## Текущая электроника

Два TT, L298N, позиционный SG90, три фоторезистора и две кнопки. Поддерживается ATmega328P / 16 МГц. Нужны отдельные проверенные источники питания моторов и SG90 и общий GND. Схема и последовательность подключения находятся в иллюстрированной инструкции.

## Что проверено

Проверены сборка прошивки для UNO и Nano, автоматические сценарии, ручное управление и экспорт настроек, соответствие встроенных моделей STL и геометрия исправленного узла качалки. C++-адаптер оборудования исполнялся в AVR-эмуляторе с моделями GPIO, EEPROM и серво. Физическая загрузка через браузер и грузоподъёмность ещё требуют испытаний на настоящем роботе.

Симуляция приближённая: она не рассчитывает прочность, массу, сцепление колёс и реальные оптические свойства поля. Поле по картинке — схема для настройки, а не подтверждённые размеры конкурсного поля.

## Исходные материалы

`Inputs` содержит предоставленные материалы кейса и фото. `outputs/AmurCargo_Photo/User_Models` — исходное шасси пользователя, `Downloaded_Models` — использованные библиотечные модели. Источники и условия сторонних материалов перечислены в `THIRD_PARTY.md` и `outputs/AmurCargo_Photo/SOURCES.md`.

В комплекте нет старых готовых сборок, альтернативных OBJ/GLB, временных файлов, установленных библиотек и вложенных ZIP. Список файлов с контрольными суммами — `PROJECT_MANIFEST.json`.
'''
build='''# Редактирование и пересборка

## Запуск без установки

Откройте START.html. Готовый симулятор и инструкция работают без интернета. Для USB нужен Chrome или Edge с Web Serial.

## Arduino

Откройте outputs/AmurCargo_Radial/RadialRobot/RadialRobot.ino в Arduino IDE. Установите Arduino AVR Boards и Servo. UNO / Nano: ATmega328P, 16 МГц. Из симулятора можно выгрузить этот проект с выбранными параметрами; скачивание заменяет RobotConfig.h на текущую конфигурацию.

Направление серво — калибровка конкретной платы. Оно хранится в отдельной записи EEPROM с адреса 1000 и сохраняется при стирании калибровки датчиков. `servo reverse detached` / `servo normal detached`: только на остановленной плате, в нижнем логическом положении, без груза и со снятой качалкой. Поля `angle` и `servo_output` в status показывают логический и физический угол. Это не настройка геометрии симулятора.

## Пересборка HTML

Python 3.10+ и Node.js 20+. Все команды выполняются из корня проекта.

```
python work/rebuild_site.py
```

Правьте work/radial_simulator.html, work/radial_3d.js, work/world_editor.js, work/manual_panel.js, work/serial_panel.js, work/webserial_uploader.js и outputs/AmurCargo_Radial/simulation.js. Three.js и OrbitControls локальные, в work/vendor. Если бинарный образ Arduino отсутствует, сборщик извлечёт его из существующего готового HTML. Изменения C++ не попадут в бинарный образ без отдельной компиляции.

## Прошивка и общий алгоритм

Настройки/схема: work/build_radial_settings.py. Движение: RadialCore.h. Оборудование: RobotHardware.h. Обёртка WASM: WebAssembly.cpp.

Для компиляции на Windows нужны установленный пакет Arduino AVR Boards и библиотека Servo. Сборщик ищет Arduino15 в LOCALAPPDATA; можно задать ARDUINO_DATA и ARDUINO_SERVO.

```
python work/build_flash_image.py
python work/build_nano_firmware.py
python work/rebuild_site.py
```

Если меняли RadialCore.h или макет Settings: также пересоберите FirmwareCore.wasm через work/compile_radial_wasm.py. Нужен Zig в PATH или переменная ZIG. Макет настроек Web Serial фиксирован: 440 байт; при его изменении обновите упаковщик и тесты.

## CAD и печатные детали

```
python -m pip install -r requirements.txt
python work/build_removable_forks.py
python work/build_direct_servo_horn.py
python work/rebuild_site.py
```

Модели меняются параметрами в этих генераторах. Они создают актуальные STL и сетки для симулятора. Для полной базовой сборки: build_photo.py и prepare_print_kit.py; им нужны библиотечные STEP/FCStd и work/user_base_payload.json, включённые в проект. Генератор build_kit_parts.py используется как источник исходных заготовок.

## Инструкция и готовый архив

Для снимков модели и браузерных тестов:

```
npm install
npx playwright install chromium
node work/render_assembly_guide.cjs
python work/build_illustrated_assembly.py
python work/package_ready_only.py
```

Готовая инструкция содержит картинки внутри HTML. Скрипт упаковки создаёт отдельный архив только STL + HTML. В проекте сохранены исходные PNG, чтобы можно было пересобрать инструкцию.

## Проверки

```
npm test
node work/test_manual_panel.cjs
node work/test_manual_usb.cjs
node work/test_illustrated_guide.cjs
python work/test_reverse_nut.py
python work/test_removable_forks.py
```

Браузер выбирается из установленного Edge или Playwright Chromium; BROWSER_EXECUTABLE и PLAYWRIGHT_MODULE позволяют переопределить пути. Нативный тест оборудования: g++ -std=c++17 -Iwork/kit_host -Ioutputs/AmurCargo_Radial/RadialRobot work/test_radial_hardware.cpp -o hardware_test, затем запустить hardware_test. Проверки не заменяют испытаний настоящей платы и механизма.
'''
build+='\n## Новое шасси из Blender\n\nПри изменении исходного шасси откройте исходный .blend в Blender 4.5 и запустите work/export_user_base.py через --python. Он обновит work/user_base_payload.json. Затем пересоберите базовую CAD-сборку, съёмные вилы и HTML. Blender и библиотеки разработчика не включены в архив.\n'
def meta(name,text):p=M/name;p.write_text(text,encoding='utf-8');return p
files={}
def add(name,path):
 p=Path(path)
 if not p.is_file():raise FileNotFoundError(str(p))
 files[name.replace('\\','/')]=p
add('README.md',meta('README.md',readme));add('BUILD.md',meta('BUILD.md',build))
add('Shopping_short.txt',O/'Shopping_Short.txt');add('work/build_short_purchase.py',R/'work/build_short_purchase.py')
add('.gitignore',meta('.gitignore','node_modules/\n__pycache__/\n*.pyc\nwork/cadlibs/\nwork/*cache*/\nwork/radial_avr_build/\nwork/avr_hardware_test/\nwork/project_export_check/\n*.elf\n*.o\n*.zip\n'))
add('requirements.txt',meta('requirements.txt','numpy\ntrimesh==5.2.1\ncadquery-ocp==8.0.1.1.0\nPillow\n'))
add('package.json',meta('package.json',json.dumps(dict(name='amurcargo',version='1.0.0',private=True,scripts={'test':'node work/test_radial_batch.cjs && node work/test_vertical_cargo.cjs && node work/test_webserial.cjs && node work/test_nano_upload.cjs'},devDependencies={'playwright':'^1.56.0','avr8js':'0.21.1'}),indent=2)))
third='''# Сторонние материалы\n\nThree.js r128 и OrbitControls: https://github.com/mrdoob/three.js/tree/r128, MIT, лицензия в work/vendor/LICENSE_three.txt.\n\nСторонние модели: см. outputs/AmurCargo_Photo/SOURCES.md и download_manifest.json. Не назначается общая новая лицензия библиотечным моделям и пользовательскому шасси.\n\nAVR8js: https://github.com/wokwi/avr8js, MIT. Используется только в тесте исполнения адаптера. Arduino core, Servo и компиляторы устанавливаются отдельно и не вложены в комплект.\n\nДокументы и фотографии Inputs предоставлены пользователем для проекта. Происхождение каждого файла указано в PROJECT_MANIFEST.json.\n'''
add('THIRD_PARTY.md',meta('THIRD_PARTY.md',third))
start='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AmurCargo — полный проект</title><style>body{font:17px/1.6 "Segoe UI",sans-serif;background:#edf3f8;color:#19364a;margin:0}main{max-width:800px;margin:35px auto;background:white;border-radius:18px;padding:35px}a{display:block;padding:14px;margin:10px 0;background:#f1f6fb;border-radius:10px;color:#24639b;text-decoration:none}p{color:#567083}</style><main><h1>AmurCargo: полный проект</h1><p>Начните с инструкции. Готовые страницы работают без интернета.</p><a href="outputs/AmurCargo_Radial/Assembly_Guide_RU.html">1. Сборка и подключение с картинками</a><a href="outputs/AmurCargo_Radial/Open_Simulation_3D.html">2. Симулятор, настройка и прошивка</a><a href="outputs/AmurCargo_Radial/Purchase_List_RU.html">3. Покупки и состав набора</a><a href="outputs/AmurCargo_Radial/RadialRobot/RadialRobot.ino">4. Исходники Arduino</a><a href="BUILD.md">5. Редактирование и пересборка проекта</a><p>STL перечислены в инструкции. В этом полном комплекте также есть исходные CAD-заготовки и модели компонентов. Для печати используйте только актуальный список.</p></main></html>'
add('START.html',meta('START.html',start))
worknames=['build_radial_page.py','build_radial_3d.py','finalize_portable_page.py','rebuild_site.py','build_radial_settings.py','build_flash_image.py','build_nano_firmware.py','compile_radial_avr.py','compile_radial_wasm.py','build_removable_forks.py','build_direct_servo_horn.py','build_photo.py','rigid_mounts.py','build_kit_parts.py','prepare_print_kit.py','build_quick_guide.py','build_calibration_guide.py','build_purchase_list.py','build_illustrated_assembly.py','render_assembly_guide.cjs','package_ready_only.py','package_full_project.py','radial_simulator.html','radial_3d.js','world_editor.js','manual_panel.js','serial_panel.js','webserial_uploader.js','project_export.js','runtime_paths.cjs','quick_guide_body.html','calibration_guide_body.html','user_base_payload.json','test_radial_hardware.cpp','test_radial_batch.cjs','test_radial_sim.cjs','test_webserial.cjs','test_nano_upload.cjs','test_project_export.cjs','test_manual_panel.cjs','test_manual_usb.cjs','test_illustrated_guide.cjs','test_current_model.cjs','test_field_stability.cjs','test_simple_help.cjs','test_vertical_cargo.cjs','test_radial_3d.cjs','test_world_editor.cjs','test_removable_forks.py','test_reverse_nut.py','audit_current_simulator_model.py']
for name in worknames:add('work/'+name,R/'work'/name)
for name in ['Arduino.h','EEPROM.h','Servo.h']:add('work/kit_host/'+name,R/'work/kit_host'/name)
for p in (R/'work/assembly_illustrations').glob('*.png'):add('work/assembly_illustrations/'+p.name,p)
for p in (R/'work/vendor').iterdir():
 if p.is_file():add('work/vendor/'+p.name,p)
for p in (O/'RadialRobot').iterdir():
 if p.suffix in ('.h','.ino'):add('outputs/AmurCargo_Radial/RadialRobot/'+p.name,p)
for name in ['Open_Simulation_3D.html','Assembly_Guide_RU.html','Purchase_List_RU.html','simulation.js','settings_schema.json','WebAssembly.cpp','FirmwareCore.wasm','Flash_Image.json','Flash_Image_Nano.json','Fork_Adaptation_Meshes.json','Servo_Horn_Mesh.json','Servo_Link_Meshes.json','Fork_Adaptation_Checks.json','Servo_Horn_Checks.json','Reverse_Nut_Checks.json','Current_Model_Audit.json','Hardware_Adapter_Checks.json','AVR_Build_Checks.json','Nano_Build_Checks.json','Manual_Panel_Checks.json','Illustrated_Guide_Checks.json']:
 add('outputs/AmurCargo_Radial/'+name,O/name)
manifest=json.loads((P/'Print_Ready/PRINT_MANIFEST.json').read_text(encoding='utf-8'))
add('outputs/AmurCargo_Photo/Print_Ready/PRINT_MANIFEST.json',P/'Print_Ready/PRINT_MANIFEST.json')
active=[p for p in manifest if p['file'] not in ('01_Fork_Pair_TipStops.stl','05_Crank_R18_Trial.stl')]
for item in active:add('outputs/AmurCargo_Photo/Print_Ready/'+item['file'],P/'Print_Ready'/item['file'])
for name in ['00_Fit_Coupon.stl','00_Guide_Rail.stl','00_Guide_Slider.stl']:add('outputs/AmurCargo_Photo/Print_Ready/'+name,P/'Print_Ready'/name)
for p in (O/'Fork_Adapters').glob('*_Print_Orientation.stl'):add('outputs/AmurCargo_Radial/Fork_Adapters/'+p.name,p)
for p in (O/'Fork_Adapters').glob('*.step'):add('outputs/AmurCargo_Radial/Fork_Adapters/'+p.name,p)
for p in (O/'Servo_Horn').glob('SG90_Integrated_R18_*.stl'):add('outputs/AmurCargo_Radial/Servo_Horn/'+p.name,p)
add('outputs/AmurCargo_Radial/Servo_Horn/00_SG90_Spline_Fit_Test.stl',O/'Servo_Horn/00_SG90_Spline_Fit_Test.stl')
for p in (P/'Print_Parts').glob('*.step'):
 if p.name not in ('01_Fork_Pair_TipStops.step','05_Crank_R18_Trial.step'):add('outputs/AmurCargo_Photo/Print_Parts/'+p.name,p)
base_ast=ast.parse((R/'work/build_photo.py').read_text(encoding='utf-8'))
used_models={'UNO_R3.FCStd'}
for node in ast.walk(base_ast):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='step' and node.args and isinstance(node.args[0],ast.Constant):used_models.add(node.args[0].value)
for p in (P/'Downloaded_Models').iterdir():
 if p.is_file() and (p.name in used_models or p.suffix.lower() in ('.md','.txt')):add('outputs/AmurCargo_Photo/Downloaded_Models/'+p.name,p)
for name in ['assembly_data.json','SOURCES.md','download_manifest.json','Printability_Checks.json','component_manifest.json']:add('outputs/AmurCargo_Photo/'+name,P/name)
for p in (P/'User_Models').iterdir():
 if p.is_file():add('outputs/AmurCargo_Photo/User_Models/'+p.name,p)
inputs={'Case.pdf':'Кейс Комсомольский-на-Амуре авиационный завод  имени Ю. А. Гагарина.pdf','Case_Details.docx':'Кейс для КнААЗ(1).docx','Criteria.docx':'Критерии оценивания(1).docx','Equipment.docx':'КнААЗ оборудование.docx'}
for dest,name in inputs.items():
 source=R/'Inputs'/dest
 if not source.exists():source=Path('D:/Users/Админ/Downloads')/name
 add('Inputs/'+dest,source)
for i,name in enumerate(['47208174-8d14-4b7b-a31a-6b8286c65bf2.jfif','95c9178a-71f6-4849-b902-9333e1a8d832.jfif','0bdde3d6-95af-494f-8591-c1dfa6057a4f.jfif'],1):
 source=R/f'Inputs/Cargo_{i}.jfif'
 if not source.exists():source=Path('D:/Users/Админ/Downloads')/name
 if source.exists():add(f'Inputs/Cargo_{i}.jfif',source)
add('Inputs/Similar_Radial_Field.png',R/'outputs/Field_Research/Similar_Radial_Field.png')
for name in ['export_user_base.py','export_pickup_samples.cjs','audit_full_mechanics.py','build_hardware_runtime_test.py','test_hardware_runtime.cjs','test_servo_direction_ui.cjs','test_exported_project.py']:add('work/'+name,R/'work'/name)
for name in ['Full_Mechanical_Audit.json','Removable_Fork_Mounting_Checks.json','Pickup_Geometry_Samples.json']:add('outputs/AmurCargo_Radial/'+name,O/name)
# The full source bundle uses textual STL so changes can be inspected in Git.
# Coordinates round-trip exactly to the original float32 values; one STL only.
for name,p in list(files.items()):
 if p.suffix.lower()!='.stl':continue
 data=p.read_bytes()
 if len(data)<84:continue
 n=struct.unpack_from('<I',data,80)[0]
 if 84+50*n!=len(data):continue
 lines=['solid AmurCargo']
 for i in range(n):
  values=struct.unpack_from('<12f',data,84+i*50);numbers=[format(v,'.9g') for v in values]
  assert all(struct.pack('<f',float(s))==struct.pack('<f',v) for s,v in zip(numbers,values))
  lines+=[' facet normal '+' '.join(numbers[:3]),'  outer loop']+['   vertex '+' '.join(numbers[j:j+3]) for j in (3,6,9)]+['  endloop',' endfacet']
 lines.append('endsolid AmurCargo');out=M/'ascii_stl'/p.name;out.parent.mkdir(exist_ok=True);out.write_text('\n'.join(lines)+'\n',encoding='ascii');files[name]=out
seen={};records=[];aliases=[]
for name,p in files.items():
 data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
 if sha in seen:
  aliases.append({'omitted_duplicate':name,'same_as':seen[sha]});continue
 seen[sha]=name;records.append(dict(path=name,source_path=str(p),bytes=len(data),sha256=sha))
public=dict(format=1,project='AmurCargo',revision='R4',files=[{k:v for k,v in r.items() if k!='source_path'} for r in records],identical_files_omitted=aliases)
mp=meta('PROJECT_MANIFEST.json',json.dumps(public,ensure_ascii=False,indent=2));records.append(dict(path='PROJECT_MANIFEST.json',source_path=str(mp),bytes=mp.stat().st_size,sha256=hashlib.sha256(mp.read_bytes()).hexdigest()))
(M/'upload_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
archive=R/'outputs/AmurCargo_Full_Project_R4.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for item in records:z.write(item['source_path'],item['path'])
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(dict(files=len(records),bytes=archive.stat().st_size,raw_bytes=sum(x['bytes'] for x in records),identical_files_omitted=len(aliases),archive=str(archive)),ensure_ascii=False))
