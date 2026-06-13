# -*- coding: utf-8 -*-
"""
Run this script from terminal AFTER opening and closing REAPER at least once:

    python3 reaper_side_enable_server.py

Patches reaper.ini and reaper-kb.ini directly (bypasses reapy configparser
bug with Python 3.13). Adds:
  1. Python ReaScript support pointing to miniconda libpython3.13.dylib
  2. Web interface on port 2307 for reapy dist API
  3. activate_reapy_server ReaScript action

Restart REAPER after running.
"""
import os
import sys

# Force UTF-8 for all I/O regardless of locale
if sys.stdout.encoding and sys.stdout.encoding.lower() == "ascii":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
if sys.stderr.encoding and sys.stderr.encoding.lower() == "ascii":
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REAPER_INI = os.path.expanduser(
    "~/Library/Application Support/REAPER/reaper.ini"
)
REAPER_KB_INI = os.path.expanduser(
    "~/Library/Application Support/REAPER/reaper-kb.ini"
)
PYTHON_DYLIB_DIR = "/opt/homebrew/Caskroom/miniconda/base/lib"
PYTHON_DYLIB = "libpython3.13.dylib"
REAPY_PORT = 2307

# Find activate_reapy_server.py in reapy package
import reapy as _reapy_pkg  # type: ignore[import-untyped]
_reapy_file: str = _reapy_pkg.__file__ or ""
_reapy_dir = os.path.dirname(_reapy_file)
_reascript = os.path.join(_reapy_dir, "reascripts", "activate_reapy_server.py")
if not os.path.exists(_reascript):
    print("ERROR: activate_reapy_server.py not found at " + _reascript)
    sys.exit(1)


def read_ini(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    sections = {}
    current = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1].lower()
                sections.setdefault(current, [])
            elif current is not None:
                sections[current].append(line)
    return sections


def write_ini(path, sections):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for section, lines in sections.items():
            f.write("[" + section + "]\n")
            for line in lines:
                f.write(line + "\n")


def set_key(sections, section, key, value):
    section = section.lower()
    sections.setdefault(section, [])
    key_lower = key.lower()
    for i, line in enumerate(sections[section]):
        if "=" in line and line.split("=", 1)[0].strip().lower() == key_lower:
            sections[section][i] = key + "=" + value
            return
    sections[section].append(key + "=" + value)


def get_key(sections, section, key):
    section = section.lower()
    key_lower = key.lower()
    for line in sections.get(section, []):
        if "=" in line and line.split("=", 1)[0].strip().lower() == key_lower:
            return line.split("=", 1)[1].strip()
    return None


# patch reaper.ini
if os.path.getsize(REAPER_INI) == 0:
    print(
        "reaper.ini is empty - open REAPER once, close it, then re-run this script."
    )
    sys.exit(1)

sections = read_ini(REAPER_INI)

# 1. Enable Python ReaScript
set_key(sections, "reaper", "reascript", "1")
set_key(sections, "reaper", "reascript_pythonpath", PYTHON_DYLIB_DIR)
set_key(sections, "reaper", "reascript_pythondll", PYTHON_DYLIB)

# 2. Web interface for reapy (port 2307)
already = any(
    str(REAPY_PORT) in (get_key(sections, "reaper", "csurf_descr" + str(i)) or "")
    for i in range(10)
)

if not already:
    idx = 0
    while get_key(sections, "reaper", "csurf_descr" + str(idx)) is not None:
        idx += 1
    set_key(sections, "reaper", "csurf_descr" + str(idx),
            "Web interface  '" + str(REAPY_PORT) + "' '' 0 ''")
    set_key(sections, "reaper", "csurf_cnt", str(idx + 1))

# 3. External state so reapy knows it's configured
set_key(sections, "ext_reapy", "activate_reapy_server", _reascript)

write_ini(REAPER_INI, sections)
print("reaper.ini patched: Python=" + PYTHON_DYLIB + ", web interface port=" + str(REAPY_PORT))

# patch reaper-kb.ini
kb_sections = read_ini(REAPER_KB_INI)
action_line = 'SCR 4 0 RS_reapy_server "Script: activate_reapy_server.py" ' + _reascript

already_kb = any(
    "activate_reapy_server" in line
    for line in kb_sections.get("reaper_keys", [])
)
if not already_kb:
    kb_sections.setdefault("reaper_keys", []).append(action_line)
    write_ini(REAPER_KB_INI, kb_sections)
    print("reaper-kb.ini patched: activate_reapy_server action registered")
else:
    print("reaper-kb.ini: action already registered")

print("\nDone. Restart REAPER, then run the MCP server.")
