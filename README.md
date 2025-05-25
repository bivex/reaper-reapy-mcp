# Reaper and MCP or AI integration

A Python application for controlling REAPER Digital Audio Workstation (DAW) using the MCP(Model context protocol).

![REAPER MCP Demo](docs/media/reaper-reapy-mcp-demo-for-gif-002.gif)

## Features

- Track management (create, rename, color)
- FX management (add, remove, parameter control)
- Project tempo control
- Region and marker management
- Master track control
- MIDI operations (create items, add notes, clear items)
- Audio item operations (insert, duplicate, modify)
- MCP (Message Control Protocol) integration for remote control

## Requirements

- Python 3.7+
- REAPER DAW
- `python-reapy` Python module
- `mcp[cli]` package for MCP server
- Internet connection (for downloading sample audio file)

## Installation

1. Install REAPER if you haven't already
2. Enable reapy server via REAPER scripting
    add reaper_side_enable_server.py to reaper actions and run it inside reaper studio
3. Install current package:
4. Enable python in REAPER



The wheel package includes all necessary dependencies and can be used in other Python projects that need REAPER integration. The project uses `pyproject.toml` for modern Python packaging configuration, which provides better dependency management and build system configuration.

### Sample Audio File
The application uses a sample MP3 file for testing audio operations. The file will be automatically downloaded when needed from:
```
https://www2.cs.uic.edu/~i101/SoundFiles/StarWars3.mp3
```

This is a short Star Wars theme clip that's commonly used for testing audio applications.

### Running the Server

You can run the server using uv directly:
```bash
uv --directory <project_path> run -m src.run_mcp_server
```

For example, on Windows:
```bash
uv --directory C:\path\to\guitar_pro_mcp2 run -m src.run_mcp_server
```

Or using the Python module directly after installation:
```bash
python -m src.run_mcp_server
```

### Use the MCP inspector to test the tools:
   ```bash
   test_mcp.bat
   ```

Available MCP tools:

#### Track Management
- `test_connection`: Verify connection to REAPER
- `create_track`: Create a new track
- `rename_track`: Rename an existing track
- `set_track_color`: Set track color
- `get_track_color`: Get track color

#### FX Management
- `add_fx`: Add an FX to a track
- `remove_fx`: Remove an FX from a track
- `set_fx_param`: Set FX parameter value
- `get_fx_param`: Get FX parameter value
- `get_fx_param_list`: Get list of FX parameters
- `get_fx_list`: Get list of FX on a track
- `get_available_fx_list`: Get list of available FX plugins
- `toggle_fx`: Toggle FX enable/disable state

#### Project Control
- `set_tempo`: Set project tempo
- `get_tempo`: Get current tempo
- `create_region`: Create a region
- `delete_region`: Delete a region
- `create_marker`: Create a marker
- `delete_marker`: Delete a marker

#### Master Track
- `get_master_track`: Get master track information
- `set_master_volume`: Set master track volume
- `set_master_pan`: Set master track pan
- `toggle_master_mute`: Toggle master track mute
- `toggle_master_solo`: Toggle master track solo

#### MIDI Operations
- `create_midi_item`: Create an empty MIDI item on a track
- `add_midi_note`: Add a MIDI note to a MIDI item
- `clear_midi_item`: Clear all MIDI notes from a MIDI item

#### Audio Item Operations
- `insert_audio_item`: Insert an audio file as a media item
- `duplicate_item`: Duplicate an existing item
- `get_item_properties`: Get properties of a media item
- `set_item_position`: Set the position of a media item
- `set_item_length`: Set the length of a media item
- `delete_item`: Delete a media item
- `get_items_in_time_range`: Get items within a time range

### Item ID System
All item operations use a sequential index system (0..n) for item identification. This makes it easier to work with items in scripts and automation:
- Item IDs are zero-based indices
- Each track maintains its own sequence of item indices
- Indices are stable until items are deleted or reordered
- All item operations (MIDI, audio, properties) use the same indexing system

### Claude configuration (with uv run):
```json
{
    "mcpServers": {
        "reaper-reapy-mcp": {
            "type": "stdio",
            "command": "uv",
            "args": [
                "--directory",
                "<path to folder>",
                "run",
                "-m",
                "src.run_mcp_server"
            ]
        }
    }
}
```

### Claude configuration direct:
```json
{
    "mcpServers": {
        "reaper-reapy-mcp": {
            "type": "stdio",
            "command": "python",
            "args": [
                "<path to folder>\\src\\run_mcp_server.py"
            ]
        }
    }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.