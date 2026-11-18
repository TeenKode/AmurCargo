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

Правьте tools/radial_simulator.html, tools/radial_3d.js, tools/world_editor.js, tools/manual_panel.js, tools/serial_panel.js, tools/webserial_uploader.js и simulator/simulation.js. Three.js и OrbitControls локальные, в tools/vendor. Сборщик использует встроенный образ Arduino, когда локальных BIN-файлов нет. Он проверяет отпечатки исходников и контрольные суммы AVR и WASM перед сборкой HTML. После изменения прошивки сначала пересоберите соответствующие образы командами ниже.

## Прошивка и общий алгоритм

Настройки/схема: tools/build_radial_settings.py. Движение: RadialCore.h. Оборудование: RobotHardware.h. Обёртка WASM: WebAssembly.cpp.

Для компиляции нужны Arduino AVR Boards 1.8.6 и Servo 1.2.2. Укажите ARDUINO_DATA (каталог Arduino15) и, если библиотека установлена отдельно, ARDUINO_SERVO (путь к Servo). На Windows по умолчанию используется Arduino15 из LOCALAPPDATA.

```
python tools/build_flash_image.py
python tools/build_nano_firmware.py
python tools/rebuild_site.py
```

Если меняли RadialCore.h, Settings.h, RobotConfig.h или WebAssembly.cpp, до пересборки HTML запустите также python tools/compile_radial_wasm.py (Zig 0.13.0). Нужен Zig в PATH или переменная ZIG. Макет настроек Web Serial фиксирован: 440 байт; при его изменении обновите упаковщик и тесты.

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

GitHub Actions проверяет опубликованные образы, собирает прошивку заново, запускает тесты симуляции, браузера и CAD и прикладывает готовый ZIP к успешному запуску.

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
