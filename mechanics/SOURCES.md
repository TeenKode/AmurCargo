# Источники и точность моделей

Исходное шасси, моторы с колёсами и опорный ролик взяты из предоставленного пользователем 2wd_robot.zip. Геометрия четырёх объектов сохранена без изменения размеров. Ролик опущен на 5,313 мм и дополнительно смещён на −0,139 мм по X и −0,247 мм по Y для согласования отверстий; добавлена проставка. Исходный Blender сохранён отдельно без изменений. Его лицензия неизвестна; это не разрешение на распространение.

## Скачанные модели в сборке

| Файл | Страница исходника |
|---|---|
| SG90.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electrical%20Parts/Servos/SG-90/Servo-sg90.step) |
| SG90_Horn.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electrical%20Parts/Servos/SG-90/SG90-1-arm-horn.step) |
| L298N.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electrical%20Parts/Motor%20Drivers/L298N/L298N.step) |
| UNO_R3.FCStd | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Computing/SingleBoardComputers/Arduino/Arduino%20UNO/Arduino%20UNO.FCStd) |
| Photoresistor.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electronics%20Parts/Photoresistor/Photoresistor.step) |
| LED_3mm.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electronics%20Parts/LEDs/led-3mm-short.step) |
| Tactile_Button.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electronics%20Parts/Buttons/THT/pushbutton-mini.step) |
| Resistor_220.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Electronics%20Parts/Resistors/res-1_4w-220ohm.step) |
| Screw_M3x12.step | [Источник](https://github.com/FreeCAD/FreeCAD-library/blob/master/Mechanical%20Parts/Fasteners/Bolts%20%26%20Screws/Metric/ISO4762_Hex_Socket_Head_Cap_Screw_M3x12.step) |
| 18650_Holder_Keystone.step | [KiCad Battery models](https://kicad.github.io/packages3d/Battery.html) |

Модели FreeCAD-library: авторы библиотеки, CC BY 3.0; сведения об авторах находятся в истории исходных файлов. KiCad: CC BY-SA 4.0 с исключением для проектов. Three.js r128 и OrbitControls: MIT. Тексты лицензий сохранены в Downloaded_Models. Полные адреса, размеры файлов и контрольные суммы — в download_manifest.json.

## Авторские детали и замены

- Подъёмник, вилы, крепления, площадка, стойки и рычаг — авторская геометрия.
- Винты вил M3×10 представлены производной от M3×12 с удалением 2 мм конца стержня; без растяжения модели.
- Четыре аккумулятора: авторский номинальный габарит 18×65 мм. Скачанный защищённый элемент длиной 69 мм не использован.
- Четыре одиночных держателя Keystone заменяют неустановленный общий держатель.
- UNO R3 — типовая замена платы CH340G; один мелкий элемент исходного FCStd не прочитался и пропущен, оригинал сохранён.
- L298N — условная модель драйвера: пользователь подтвердил наличие драйвера, но не его марку.
- MB-102 — габаритная модель 165×55 мм.
- Груз: внешний размер точный по заданию, внутренние размеры оценены по трём фотографиям.
- Остальные скачанные файлы оставлены как справочные образцы. TT_Motor.step, Wheel_65mm.step и Dupont_1x3.step в новой сборке не используются.
- STEP сборки содержит упрощённые габаритные тела вместо исходной сетки шасси и мелких частей Arduino. Точная сетка — в Blender, GLB, OBJ и HTML.