# Подключение REAPER к MCP

## Настройка REAPER

### 1. Включить Python в REAPER
```
Options → Preferences → Plug-ins → ReaScript
✓ Enable Python for use with ReaScript
```

**macOS (miniconda, Python 3.13):**
```
Custom path to Python dylib directory:
  /opt/homebrew/Caskroom/miniconda/base/lib

Force ReaScript to use specific Python dylib:
  libpython3.13.dylib
```

Если 3.13 не работает — попробуй env `omni` (Python 3.12):
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

### 2. Активировать reapy сервер в REAPER
**Способ A:** Actions → Load ReaScript → выберите `reaper_side_enable_server.py`

**Способ B:** Запусти из командной строки:
```bash
python reaper_side_enable_server.py
```

### 3. Перезапусти REAPER

### 4. Запусти MCP сервер (в отдельном терминале)
```bash
uv run -m src.run_mcp_server
# или
python -m src.run_mcp_server
```

### Проверка соединения
```bash
python start_reapy_server_simple.py
```
Должно показать: "✅ Connection established successfully!"


