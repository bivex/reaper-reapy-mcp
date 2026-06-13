# Подключение REAPER к MCP (macOS)

## Полный порядок настройки

### 1. Установить зависимости
```bash
pip install -e .
pip install python-reapy
```

### 2. Включить Python в REAPER

Options -> Preferences -> Plug-ins -> ReaScript
- Enable Python for use with ReaScript: включить

**macOS (miniconda, Python 3.13):**
```
Custom path to Python dylib directory:
  /opt/homebrew/Caskroom/miniconda/base/lib

Force ReaScript to use specific Python dylib:
  libpython3.13.dylib
```

Если 3.13 не работает -- env `omni` (Python 3.12):
```
Custom path to Python dylib directory:
  /opt/homebrew/Caskroom/miniconda/base/envs/omni/lib

Force ReaScript to use specific Python dylib:
  libpython3.12.dylib
```

**Windows (anaconda):**
```
Custom path: C:\ProgramData\anaconda3
DLL name: python312.dll
```

### 3. Настроить reapy (один раз, из терминала)

REAPER может быть закрыт или запущен (один экземпляр):
```bash
python3 reaper_side_enable_server.py
```

Скрипт патчит reaper.ini напрямую, обходя баг configparser в Python 3.13.

### 4. Включить Web Interface в REAPER

Options -> Preferences -> Control/OSC/web -> Add -> Web browser interface
- Port: 2307
- OK -> Apply

Без этого reapy dist API не подключится.

### 5. Активировать reapy сервер в REAPER

Actions -> Run ReaScript -> выбрать `activate_reapy_server.py` из корня проекта.

Нужно запускать каждый раз при старте REAPER (или добавить в startup actions).

### 6. Запустить MCP сервер
```bash
python3 src/run_mcp_server.py
```

### 7. Проверить соединение
```bash
python3 -c "import warnings; warnings.filterwarnings('ignore'); import reapy; print('tracks:', reapy.Project().n_tracks)"
```

Должно вывести количество треков в открытом проекте.

## Известные проблемы

**MemoryError в REAPER при запуске activate_reapy_server.py**
Возникает если что-то делает голый TCP connect к порту 2306 (reapy server).
Решение: не использовать сырые сокеты для проверки порта -- только reapy API.

**AttributeError: module 'reapy.reascript_api' has no attribute 'EnumProjects'**
reapy не подключился к серверу. Проверить:
- Web interface на 2307 запущен (шаг 4)
- activate_reapy_server.py выполнен в REAPER (шаг 5)

**Script execution error: UnicodeDecodeError ascii**
REAPER запускает скрипт с ASCII локалью.
Решение: запускать reaper_side_enable_server.py только из терминала, не из REAPER.

**reaper.ini is empty**
Открыть REAPER, закрыть его, затем запустить скрипт снова.
