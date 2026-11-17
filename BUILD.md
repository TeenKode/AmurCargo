# Редактирование и пересборка

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

## Новое шасси из Blender

При изменении исходного шасси откройте исходный .blend в Blender 4.5 и запустите work/export_user_base.py через --python. Он обновит work/user_base_payload.json. Затем пересоберите базовую CAD-сборку, съёмные вилы и HTML. Blender и библиотеки разработчика не включены в архив.
