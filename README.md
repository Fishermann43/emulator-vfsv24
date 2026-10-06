# Эмулятор оболочки ОС. Вариант 24

## Этап 1: Графический REPL
Графическое окно (tkinter), заголовок содержит имя VFS.
Парсер раскрывает переменные окружения (`$HOME`).
Команды `ls` и `cd` — заглушки, `exit` закрывает окно.

## Запуск

```text
python3 src/emulator.py
```
## Этап 2: Конфигурация
Параметры командной строки `--vfs` и `--script`, отладочный вывод
параметров при запуске. Стартовый скрипт выполняется с показом
ввода и вывода и останавливается при первой ошибке.

## Запуск

```text
python3 src/emulator.py --vfs vfs.xml
python3 src/emulator.py --vfs vfs.xml --script scripts/startup_commands.txt
```

## Этап 3: VFS из XML
Виртуальная файловая система хранится в XML и при запуске
полностью загружается в память. Двоичные данные — в base64.
Ошибки загрузки (нет файла, неверный формат) показываются
в окне эмулятора.

## Запуск

```text
python3 src/emulator.py --vfs vfs.xml
python3 src/emulator.py --vfs vfs.xml --script scripts/startup_commands.txt
```

Варианты VFS: `vfs-min.xml`, `vfs-files.xml`, `vfs-deep.xml`
(несколько уровней каталогов). Скрипты `scripts/test_min.*`,
`scripts/test_files.*`, `scripts/test_deep.*` проверяют работу
с каждым вариантом.

## Этап 4: Основные команды
Команды `ls` и `cd` работают с объектом VFS. Новые команды:
`cat` (содержимое файла) и `uniq` (убрать соседние повторы,
с флагом `-c` показывает счетчики).

## Запуск

```text
python3 src/emulator.py --vfs vfs.xml
python3 src/emulator.py --vfs vfs.xml --script scripts/startup_commands.txt
```

Варианты VFS: `vfs-min.xml`, `vfs-files.xml`, `vfs-deep.xml`
(несколько уровней каталогов). Скрипты `scripts/test_min.*`,
`scripts/test_files.*`, `scripts/test_deep.*` проверяют работу
с каждым вариантом.
