# Редактирование и пересборка

## Запуск без установки

Откройте START.html. Готовый симулятор и инструкция работают без интернета. Для USB нужен Chrome или Edge с Web Serial.

## Arduino

Откройте firmware/RadialRobot/RadialRobot.ino в Arduino IDE. Установите Arduino AVR Boards и Servo. UNO / Nano: ATmega328P, 16 МГц. Из симулятора можно выгрузить этот проект с выбранными параметрами; скачивание заменяет RobotConfig.h на текущую конфигурацию.

Направление серво — калибровка конкретной платы. Оно хранится в отдельной записи EEPROM с адреса 1000 и сохраняется при стирании калибровки датчиков. `servo reverse detached` / `servo normal detached`: только на остановленной плате, в нижнем логическом положении, без груза и со снятой качалкой. Поля `angle` и `servo_output` в status показывают логический и физический угол. Это не настройка геометрии симулятора.

## Пересборка HTML

Python 3.10+ и Node.js 20+. Все команды выполняются из корня проекта.

```
python tools/rebuild_site.py
```

Правьте tools/radial_simulator.html, tools/radial_3d.js, tools/world_editor.js, tools/manual_panel.js, tools/serial_panel.js, tools/webserial_uploader.js и simulator/simulation.js. Three.js и OrbitControls локальные, в tools/vendor. Сборщик проверяет образы AVR и WASM в `firmware/build`, пересобирает устаревшие файлы и встраивает их в HTML. Копии в HTML нельзя редактировать отдельно от исходников.

## Прошивка и общий алгоритм

Единое место исходников прошивки — `firmware/RadialRobot/`: общий алгоритм `RadialCore.h`, аппаратный адаптер Arduino `RobotHardware.h`, WASM-обёртка `firmware/wasm/WebAssembly.cpp`. Компилированные образы и манифесты хранятся в `firmware/build/`. Автономный HTML содержит *сгенерированную*, а не редактируемую копию прошивки. Генератор схемы настроек: `tools/build_radial_settings.py`.

Для компиляции нужны Arduino AVR Boards 1.8.6 и Servo 1.2.2. Укажите ARDUINO_DATA (каталог Arduino15) и, если библиотека установлена отдельно, ARDUINO_SERVO (путь к Servo). На Windows по умолчанию используется Arduino15 из LOCALAPPDATA.

```
python tools/rebuild_site.py
```

`rebuild_site.py` автоматически проверяет отпечатки источников и при изменениях пересобирает UNO, Nano и WASM. Для WASM требуется Zig 0.13.0 в PATH или переменная ZIG. Исходники и параметры настройки находятся в одном месте, а `firmware/build` и HTML — только сборочные результаты. Нужен Zig в PATH или переменная ZIG. Макет настроек Web Serial фиксирован: 440 байт; при его изменении обновите упаковщик и тесты.

## CAD и печатные детали

```
python -m pip install -r requirements.txt
python tools/build_removable_forks.py
python tools/build_direct_servo_horn.py
python tools/rebuild_site.py
```

Модели меняются параметрами в этих генераторах. Они создают актуальные STL и сетки для симулятора. Для полной базовой сборки: build_photo.py и prepare_print_kit.py; им нужны библиотечные STEP/FCStd и mechanics/user_base_payload.json, включённые в проект. Генератор build_kit_parts.py используется как источник исходных заготовок.

## Инструкция и готовый архив

Для снимков модели и браузерных тестов:

```
npm ci
npx playwright install chromium
node tools/render_assembly_guide.cjs
python tools/build_illustrated_assembly.py
python tools/package_ready_only.py
```

Готовая инструкция содержит картинки внутри HTML. Скрипт упаковки создаёт отдельный архив только STL + HTML. В проекте сохранены исходные PNG, чтобы можно было пересобрать инструкцию.

## Проверки

GitHub Actions собирает прошивку из единых исходников, проверяет симуляцию, USB, браузер и CAD, а также проверяет соответствие встроенных образов в автономном HTML. Только после успешных тестов запуск `push` автоматически публикует в *эту же ветку* обновлённый `simulator/Open_Simulation_3D.html`, проверенные UNO/Nano BIN/HEX и WASM с манифестами. В PR из форков запись запрещена; публикация никогда не запускается из события `pull_request`. Если ветка успела измениться, старый результат не перезаписывает новую версию. Готовый ZIP сохраняется в артефактах Actions. `main` обновится только после слияния PR.

```
python tools/rebuild_site.py
npm test
node tools/test_manual_panel.cjs
node tools/test_manual_usb.cjs
node tools/test_serial_reconnect.cjs
node tools/test_illustrated_guide.cjs
python tools/test_reverse_nut.py
python tools/test_removable_forks.py
```

Браузер выбирается из установленного Edge или Playwright Chromium; BROWSER_EXECUTABLE и PLAYWRIGHT_MODULE позволяют переопределить пути. Нативный тест оборудования: g++ -std=c++17 -Itools/kit_host -Ifirmware/RadialRobot tools/test_radial_hardware.cpp -o hardware_test, затем запустить hardware_test. Проверки не заменяют испытаний настоящей платы и механизма.

## Новое шасси из Blender

При изменении исходного шасси откройте исходный .blend в Blender 4.5 и запустите tools/export_user_base.py через --python. Он обновит mechanics/user_base_payload.json. Затем пересоберите базовую CAD-сборку, съёмные вилы и HTML. Blender и библиотеки разработчика не включены в архив.

## Калибровка реального подъёмника

Вкладка «Робот · USB» → «Сервопривод». Команда `angle N` задаёт пробный логический угол. `limits LOW HIGH` записывает пару в EEPROM после остановки серво. Изменение направления сбрасывает пару к значениям прошивки. `status` показывает целевой и командный углы, границы и кнопки. `stream on` и `stream off` управляют телеметрией.

## Испытания движения по линии и проверка пропуска луча

В `HUB_TURN` угол пока оценивается по времени, но теперь `HUB_EXIT` начинает корректировать движение по датчикам, когда робот отъехал от центрального круга. `ACQUIRE` принимает найденный луч только после непрерывного показания в течение `TURN_LINE_MS`. Без линии робот кратко продвигается на малом PWM, затем ограниченно сканирует в обе стороны, а после `ACQUIRE_MS` останавливается с `EXIT_TIMEOUT`.

Перед испытанием закрепите робота на подставке с вывешенными колёсами и проверьте направление каждого двигателя и кнопку STOP. Затем на ровном свободном участке проверьте старт, прохождение прямой и изгиба без груза; отдельными тестами — краткий разрыв линии, уход с луча после поворота, широкую отметку и движение с грузом. При ложном срабатывании, сильных колебаниях или ошибке линии запишите `status`/ `stream on` из вкладки «Робот · USB» и сохраните журнал; поля `raw`, `line`, `pwm`, `target`, `err`, `corr`, `dfilter`, `lost_ms`, `cal` помогут отличить освещение от проблемы регулирования. Калибровку делайте при рабочем освещении. Один отказавший датчик не всегда обнаружим однозначно без дополнительных датчиков.

## Надёжное движение по линии

`RadialCore.h` применяет ограниченный по `LOST_MS` поиск линии в сторону последнего подтверждённого отклонения, замедление в зависимости от ошибки положения и фильтр производной PD-регулятора. При потере линии без известной стороны робот после краткого осторожного движения останавливается. Когда время поиска истекает, срабатывает `LINE_LOST`. В широкой отметке управляющая коррекция сбрасывается. Эти правила действуют и на Arduino, и в WASM.

Для проверки используйте `npm test` и `g++ -std=c++17 -Ifirmware/RadialRobot tools/test_line_following.cpp -o /tmp/line-test && /tmp/line-test`. Параметры рассчитаны как стартовые; перед конкурсом проверьте реальные датчики, освещение и нагрузку.
