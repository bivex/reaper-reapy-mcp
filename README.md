# REAPER MCP Server

> Control REAPER Digital Audio Workstation through AI assistants using the Model Context Protocol (MCP)

![REAPER MCP Demo](docs/media/reaper-reapy-mcp-demo-for-gif-002.gif)

## Overview

Python-based MCP server providing comprehensive control over REAPER DAW through AI assistants. 110+ specialized tools covering tracks, effects, MIDI, audio items, routing, automation, professional mastering and mixing — all through natural language commands.

Uses [bivex/reapy](https://github.com/bivex/reapy) fork as a git submodule (`vendor/reapy`), with Python 3.13 compatibility patches applied. Operations not covered by reapy are handled via direct REAPER ReaScript API calls.

## Features

| Category | Capabilities |
|----------|-------------|
| 🎛️ **Track Management** | Create, rename, color, volume (dB), pan, mute, solo, record arm |
| 🎚️ **FX Control** | Add/remove effects, parameter automation, compressor/limiter presets |
| 🎹 **MIDI Operations** | Create items, add/edit notes, pitch filter, transpose, musical positioning |
| 🎧 **Audio Processing** | Insert files, duplicate, split, fade, crossfade, reverse |
| 🔗 **Routing & Mixing** | Sends/receives, folder tracks, bus creation, sidechain routing |
| 🎛️ **Automation** | Envelope creation, point editing, automation modes |
| 🎯 **Project Control** | Tempo, markers, regions, master track |
| 📊 **Audio Analysis** | LUFS/loudness, spectrum, stereo imaging, dynamics, true peak |
| 🎚️ **Pitch & Timestretch** | Item pitch shift (semitones), playback rate, élastique/SoundTouch modes, MIDI transpose |
| 🎬 **Render & Export** | Bounce to file, freeze/unfreeze tracks, stem export, region render |

## Quick Start

### Prerequisites

- Python 3.10+ (3.13 tested on macOS with miniconda)
- REAPER DAW installed

### 1. Clone with submodules

```bash
git clone --recurse-submodules <repository-url>
cd reaper-reapy-mcp
```

Or if already cloned:

```bash
git submodule update --init
```

### 2. Install dependencies

```bash
pip install -e .
pip install --no-build-isolation vendor/reapy
```

### 3. Configure REAPER — Enable Python for ReaScripts

**macOS (miniconda):**

In REAPER: **Options → Preferences → Plug-ins → ReaScript**
- Check **"Enable Python for use with ReaScript"**
- Custom path to Python dylib directory: `/opt/homebrew/Caskroom/miniconda/base/lib`
- Force ReaScript to use specific Python dylib: `libpython3.13.dylib`

**Windows (anaconda):**
- Custom path: `C:\ProgramData\anaconda3`
- DLL: `python312.dll`

### 4. Patch reaper.ini (run once, REAPER can be open or closed)

```bash
python3 reaper_side_enable_server.py
```

Enables the reapy web interface and patches `reaper.ini` for Python 3.13 compatibility.

### 5. Enable Web Interface in REAPER

**Options → Preferences → Control/OSC/web** → Add → **Web browser interface** → port `2307` → OK → Apply

Required for reapy dist API to connect.

### 6. Activate reapy Server in REAPER

**Actions → Run ReaScript** → select `activate_reapy_server.py` from the project root.

Run this every time REAPER starts (or add it to REAPER startup actions).

### 7. Start the MCP Server

```bash
python3 src/run_mcp_server.py
```

### 8. Verify Connection

```bash
python3 -c "import warnings; warnings.filterwarnings('ignore'); import reapy; print('tracks:', reapy.Project().n_tracks)"
```

## MCP Client Integration

### Claude Desktop

```json
{
    "mcpServers": {
        "reaper-reapy-mcp": {
            "type": "stdio",
            "command": "python3",
            "args": ["/path/to/reaper-reapy-mcp/src/run_mcp_server.py"]
        }
    }
}
```

### Cursor IDE

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "reaper-reapy-mcp": {
      "command": "python3",
      "args": ["/path/to/reaper-reapy-mcp/src/run_mcp_server.py"]
    }
  }
}
```

## Mastering & Mixing

This project is designed for professional mixing and mastering workflows. Below is what is available and what relies on direct RPR API calls instead of reapy.

### What reapy covers natively

- Track volume/pan read-write (`track.volume`, `track.pan`)
- FX chain: add, remove, reorder, parameter read/write
- Sends and receives routing
- Envelopes (automation)
- MIDI: notes, events (partial)
- Mute, solo, record arm
- Markers and regions (read)
- Tempo and time signature

### What this fork adds on top of reapy

These are not in reapy 0.10 and are implemented via direct REAPER ReaScript API:

| Feature | Controller | Notes |
|---------|-----------|-------|
| Track volume in dB | `pitch.set_track_volume_db` | reapy uses 0–1 linear; this accepts dBFS |
| Master track direct access | `master.*` | Via `RPR.GetMasterTrack` + RPR calls |
| Render / bounce to file | `render.render_project` | Uses REAPER action 42230 |
| Freeze / unfreeze track | `render.freeze_track` / `render.unfreeze_track` | Actions 41223–41225 |
| Stem export | `render.export_stems` | Solos each track, renders, restores state |
| Region render | `render.render_regions` | Render all regions to separate files |
| Item pitch shift | `pitch.set_item_pitch` | `D_PITCH` via `SetMediaItemInfo_Value` |
| Playback rate / timestretch | `pitch.set_item_rate` | `D_PLAYRATE` + `B_PPITCH` |
| Pitch algorithm (élastique etc.) | `pitch.set_take_pitch_mode` | `I_PITCHMODE` on take |
| MIDI transpose | `pitch.transpose_midi_item` | Rewrites all notes via `MIDI_SetNote` |
| LUFS / loudness analysis | `analysis.*` | Simulated via peak + RMS integration |
| Sidechain routing | `sidechain.*` | Channel 3/4 routing via RPR sends |

### Workflow Examples

**Pitch shift an audio item:**
```python
set_item_pitch(track_index=0, item_id=0, semitones=-2.0)   # down 2 semitones
set_item_rate(track_index=0, item_id=0, rate=0.9, preserve_pitch=True)
```

**Bounce a track to WAV:**
```python
bounce_track(track_index=2, output_path="/tmp/bass_bounce.wav")
```

**Freeze a CPU-heavy track:**
```python
freeze_track(track_index=1, freeze_to_stereo=True)
# ... later ...
unfreeze_track(track_index=1)
```

**Export stems:**
```python
export_stems(output_dir="/tmp/stems", track_indices=[0,1,2,3])
# Produces: /tmp/stems/Lead.wav, /tmp/stems/Violin1.wav, ...
```

**Render all regions:**
```python
render_regions(output_dir="/tmp/regions", name_pattern="$region")
```

**LUFS normalization:**
```python
normalize_track_lufs(track_index=0, target_lufs=-14.0, true_peak_ceiling=-1.0)
```

**Sidechain compression (kick → bass):**
```python
create_sidechain_send(
    source_track=0,       # Kick
    destination_track=1,  # Bass with compressor
    dest_channels=3,      # Route to channels 3/4
    level_db=-3.0
)
```

## Available Tools (110+)

<details>
<summary><strong>Connection (1)</strong></summary>

- `test_connection`
</details>

<details>
<summary><strong>Track Management (17)</strong></summary>

- `create_track`, `rename_track`, `set_track_color`, `get_track_color`
- `get_track_count`, `set_track_volume`, `get_track_volume`
- `set_track_pan`, `get_track_pan`, `set_track_mute`, `get_track_mute`
- `set_track_solo`, `get_track_solo`, `toggle_track_mute`, `toggle_track_solo`
- `set_track_arm`, `get_track_arm`
</details>

<details>
<summary><strong>FX Management (10)</strong></summary>

- `add_fx`, `remove_fx`, `set_fx_param`, `get_fx_param`
- `get_fx_param_list`, `get_fx_list`, `get_available_fx_list`, `toggle_fx`
- `set_compressor_params`, `set_limiter_params`
</details>

<details>
<summary><strong>MIDI Operations (6)</strong></summary>

- `create_midi_item`, `add_midi_note`, `clear_midi_item`
- `get_midi_notes`, `find_midi_notes_by_pitch`, `get_selected_midi_item`
</details>

<details>
<summary><strong>Audio & Items (15)</strong></summary>

- `insert_audio_item`, `duplicate_item`, `delete_item`
- `get_item_properties`, `set_item_position`, `set_item_length`
- `get_items_in_time_range`, `get_selected_items`
- `split_item`, `glue_items`, `fade_in`, `fade_out`
- `crossfade_items`, `reverse_item`, `get_item_fade_info`
</details>

<details>
<summary><strong>Pitch & Timestretch (6)</strong></summary>

- `set_item_pitch`, `get_item_pitch` — semitone pitch shift on audio items
- `set_item_rate`, `get_item_rate` — playback rate / timestretch
- `set_take_pitch_mode` — pitch algorithm (élastique, SoundTouch, DIRAC)
- `transpose_midi_item` — transpose all MIDI notes by N semitones
- `set_track_volume_db`, `get_track_volume_db` — track volume in dBFS via RPR
</details>

<details>
<summary><strong>Render & Export (6)</strong></summary>

- `render_project` — render project or time range to file
- `render_time_selection` — render current time selection
- `bounce_track` — bounce single track to WAV (solos, renders, restores)
- `freeze_track`, `unfreeze_track`, `is_frozen` — track freeze
- `render_regions` — render all regions to separate files
- `export_stems` — export each track as a separate stem file
</details>

<details>
<summary><strong>Routing & Mixing (17)</strong></summary>

- `add_send`, `remove_send`, `get_sends`, `get_receives`
- `set_send_volume`, `set_send_pan`, `toggle_send_mute`
- `get_track_routing_info`, `debug_track_routing`
- `clear_all_sends`, `clear_all_receives`
- `create_folder_track`, `create_bus_track`, `set_track_parent`
- `get_track_children`, `set_track_folder_depth`, `get_track_folder_depth`
</details>

<details>
<summary><strong>Sidechain & Bus Routing (4)</strong></summary>

- `create_sidechain_send` — sidechain routing (kick → bass compressor)
- `setup_parallel_bus` — parallel processing with phase compensation
- `add_saturation_bus` — parallel harmonic enhancement
- `sidechain_route_analyzer` — route validation and latency analysis
</details>

<details>
<summary><strong>Automation (6)</strong></summary>

- `create_automation_envelope`, `add_automation_point`
- `get_automation_points`, `set_automation_mode`
- `get_automation_mode`, `delete_automation_point`
</details>

<details>
<summary><strong>Project & Master (14)</strong></summary>

- **Project**: `set_tempo`, `get_tempo`, `clear_project`
- **Markers**: `create_region`, `delete_region`, `create_marker`, `delete_marker`
- **Master**: `get_master_track`, `set_master_volume`, `set_master_pan`, `toggle_master_mute`, `toggle_master_solo`
- **Metering**: `get_track_peak_level`, `get_master_peak_level`
</details>

<details>
<summary><strong>Professional Audio Analysis (14)</strong></summary>

- **Loudness**: `loudness_measure_track`, `loudness_measure_master`
- **Spectrum**: `spectrum_analyzer_track`, `spectrum_analyzer_master`
- **Stereo**: `phase_correlation`, `stereo_image_metrics`
- **Dynamics**: `crest_factor_track`, `crest_factor_master`
- **LUFS Normalization**: `normalize_track_lufs`, `match_loudness_between_tracks`
- **Gain Staging**: `write_volume_automation_to_target_lufs`, `clip_gain_adjust`
- **Mastering**: `comprehensive_track_analysis`, `master_chain_analysis`
</details>

## Key Concepts

### Dual Position Format

Tools accept both time and musical positioning:

| Format | Example | Use Case |
|--------|---------|----------|
| Time | `{"start_time": 15.5}` | Precise timing in seconds |
| Musical | `{"start_measure": "3:2.5"}` | Measure:beat notation |

Musical format: `"measure:beat"` (1-based, decimals supported)

### Item ID System

- Zero-based indices per track (0, 1, 2...)
- Stable until items are deleted or reordered
- Consistent across MIDI, audio, and property operations

## reapy Notes

This project uses [bivex/reapy](https://github.com/bivex/reapy) as a git submodule in `vendor/reapy`. It is a fork of the original [RomeoDespres/reapy](https://github.com/RomeoDespres/reapy) with the following patches applied:

- **PR#138**: Fix Python 3.13 `configparser._UnnamedSection` AttributeError

Operations outside reapy's scope (render, freeze, pitch, stem export, master track via RPR) are implemented directly using `reapy.reascript_api` (the raw REAPER ReaScript Python bridge).

## Troubleshooting

### ConnectionRefusedError

1. Confirm REAPER is running with web interface on port 2307
2. Run `activate_reapy_server.py` inside REAPER (Actions → Run ReaScript)
3. Check port: `lsof -i :2306 -i :2307`

### Python not found in REAPER

Check **Options → Preferences → Plug-ins → ReaScript** — path must point to the directory containing the Python dylib, not the Python binary itself.

### reapy install fails

Use `--no-build-isolation`:
```bash
pip install --no-build-isolation vendor/reapy
```

### Common Issues

| Problem | Solution |
|---------|----------|
| Port mismatch | Web interface must be on port 2307 |
| Python dylib not found | Set correct path in REAPER ReaScript prefs |
| reapy server not active | Run `activate_reapy_server.py` in REAPER Actions |
| MIDI notes return 0 | Use `get_midi_notes` — reads via RPR MIDI_CountEvts, not reapy take.notes |

## Development

```bash
# Run all tests (no REAPER needed)
pytest tests/ -q

# Run integration tests (REAPER must be running with reapy server active)
pytest tests/ -m reaper -q
```

135 tests pass offline (mock-based). 12 additional integration tests require a live REAPER connection.

## License

MIT License — see [LICENSE](LICENSE) for details.
