# Reaper and MCP or AI integration

A Python application for controlling REAPER Digital Audio Workstation (DAW) using the MCP(Model context protocol).

![REAPER MCP Demo](docs/media/reaper-reapy-mcp-demo-for-gif-002.gif)

## Features

- **Track Management**: Create, rename, and color tracks
- **FX Management**: Add, remove, and control effect parameters
- **Project Control**: Set tempo, manage regions and markers
- **Master Track Control**: Volume, pan, mute, and solo operations
- **MIDI Operations**: Create items, add/get notes, clear items with musical positioning
- **Audio Item Operations**: Insert, duplicate, modify with enhanced positioning support
- **Routing Management**: Create, manage, and control track sends and receives
- **Dual Position Format**: Support both time (seconds) and measure:beat notation
- **Reliable Duplication**: Uses REAPER's built-in commands for accurate item copying
- **MCP Integration**: Model Context Protocol server for AI assistant control

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

## Available MCP Tools

### Connection & Testing
| Tool | Description |
|------|-------------|
| `test_connection` | Verify connection to REAPER |

### Track Management
| Tool | Description |
|------|-------------|
| `create_track` | Create a new track |
| `rename_track` | Rename an existing track |
| `set_track_color` | Set track color |
| `get_track_color` | Get track color |
| `get_track_count` | Get number of tracks in project |

### Routing Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `add_send` | Add a send from source track to destination track | `source_track`, `destination_track`, `volume`, `pan`, `mute`, `phase`, `channels` |
| `remove_send` | Remove a specific send from a track | `source_track`, `send_id` |
| `get_sends` | Get all sends from a track | `track_index` |
| `get_receives` | Get all receives on a track | `track_index` |
| `set_send_volume` | Set the volume of a send | `source_track`, `send_id`, `volume` |
| `set_send_pan` | Set the pan of a send | `source_track`, `send_id`, `pan` |
| `toggle_send_mute` | Toggle or set the mute state of a send | `source_track`, `send_id`, `mute` |
| `get_track_routing_info` | Get comprehensive routing information for a track | `track_index` |
| `debug_track_routing` | Debug track routing information for troubleshooting | `track_index` |
| `clear_all_sends` | Remove all sends from a track | `track_index` |
| `clear_all_receives` | Remove all receives from a track | `track_index` |

### FX Management
| Tool | Description |
|------|-------------|
| `add_fx` | Add an FX to a track |
| `remove_fx` | Remove an FX from a track |
| `set_fx_param` | Set FX parameter value |
| `get_fx_param` | Get FX parameter value |
| `get_fx_param_list` | Get list of FX parameters |
| `get_fx_list` | Get list of FX on a track |
| `get_available_fx_list` | Get list of available FX plugins |
| `toggle_fx` | Toggle FX enable/disable state |

### Project Control
| Tool | Description |
|------|-------------|
| `set_tempo` | Set project tempo |
| `get_tempo` | Get current tempo |
| `create_region` | Create a region |
| `delete_region` | Delete a region |
| `create_marker` | Create a marker |
| `delete_marker` | Delete a marker |

### Master Track
| Tool | Description |
|------|-------------|
| `get_master_track` | Get master track information |
| `set_master_volume` | Set master track volume |
| `set_master_pan` | Set master track pan |
| `toggle_master_mute` | Toggle master track mute |
| `toggle_master_solo` | Toggle master track solo |

### MIDI Operations
| Tool | Description | Position Support |
|------|-------------|-----------------|
| `create_midi_item` | Create an empty MIDI item on a track | Time & Measure:Beat |
| `add_midi_note` | Add a MIDI note to a MIDI item | Time only |
| `get_midi_notes` | Get all MIDI notes from a MIDI item | - |
| `clear_midi_item` | Clear all MIDI notes from a MIDI item | - |
| `find_midi_notes_by_pitch` | Find MIDI notes within a pitch range | - |
| `get_selected_midi_item` | Get the currently selected MIDI item | - |

### Audio Item Operations
| Tool | Description | Position Support |
|------|-------------|-----------------|
| `insert_audio_item` | Insert an audio file as a media item | Time & Measure:Beat |
| `duplicate_item` | Duplicate an existing item (MIDI or audio) | Time & Measure:Beat |
| `get_item_properties` | Get properties of a media item | - |
| `set_item_position` | Set the position of a media item | Time & Measure:Beat |
| `set_item_length` | Set the length of a media item | - |
| `delete_item` | Delete a media item | - |
| `get_items_in_time_range` | Get items within a time range | Time & Measure:Beat |
| `get_selected_items` | Get all selected items | - |

### Item ID System
All item operations use a sequential index system (0..n) for item identification. This makes it easier to work with items in scripts and automation:
- Item IDs are zero-based indices
- Each track maintains its own sequence of item indices
- Indices are stable until items are deleted or reordered
- All item operations (MIDI, audio, properties) use the same indexing system

### Position Format Support
Many MCP tools now support dual position formats for enhanced musical workflow:

#### Time Format (seconds)
```json
{
  "start_time": 15.5,
  "new_time": 30.0
}
```

#### Measure:Beat Format
```json
{
  "start_measure": "3:2.5",
  "new_measure": "5:1"
}
```

**Format**: `"measure:beat"` where:
- `measure`: 1-based measure number
- `beat`: 1-based beat number (supports decimals)
- Example: `"4:2.5"` = measure 4, beat 2.5

#### Tools Supporting Both Formats:
- `create_midi_item` - position via `start_time` OR `start_measure`
- `insert_audio_item` - position via `start_time` OR `start_measure`  
- `duplicate_item` - position via `new_time` OR `new_measure`
- `set_item_position` - position via `new_time` OR `new_measure`
- `get_items_in_time_range` - range via time OR measure parameters

### Routing Examples

Here are some common routing scenarios using the new routing tools:

#### Basic Send Creation
```python
# Create a send from track 0 to track 1 with -6dB volume
add_send(source_track=0, destination_track=1, volume=-6.0, pan=0.0)

# Create a send with pan and mute
add_send(source_track=1, destination_track=2, volume=-3.0, pan=0.5, mute=False)
```

#### Managing Send Parameters
```python
# Set send volume
set_send_volume(source_track=0, send_id=0, volume=-12.0)

# Set send pan
set_send_pan(source_track=0, send_id=0, pan=0.25)

# Toggle send mute
toggle_send_mute(source_track=0, send_id=0)
```

#### Getting Routing Information
```python
# Get all sends from a track
get_sends(track_index=0)

# Get all receives on a track
get_receives(track_index=1)

# Get comprehensive routing info
get_track_routing_info(track_index=0)
```

#### Debugging Routing Issues
```python
# Debug routing information for troubleshooting
debug_track_routing(track_index=0)
```

#### Cleaning Up Routing
```python
# Remove all sends from a track
clear_all_sends(track_index=0)

# Remove all receives from a track
clear_all_receives(track_index=1)
```

**Note**: All routing tools are fully functional and tested. The `destination_track` field now correctly shows track indices instead of -1.0, and all send/receive operations work reliably with proper MediaTrack pointer handling.

### MCP Client Configuration

The following configurations are for different MCP clients to connect to this REAPER MCP server:

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

### Cursor MCP Configuration

To connect this MCP server to Cursor, add the following configuration to your `~/.cursor/mcp.json` file:

#### Using uv (Recommended)
```json
{
  "mcpServers": {
    "reaper-reapy-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\Admin\\Desktop\\Dev\\reaper-reapy-mcp",
        "run",
        "-m",
        "src.run_mcp_server"
      ]
    }
  }
}
```

#### Using Python directly
```json
{
  "mcpServers": {
    "reaper-reapy-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\Admin\\Desktop\\Dev\\reaper-reapy-mcp\\src\\run_mcp_server.py"
      ]
    }
  }
}
```

**Note**: Replace `C:\\Users\\Admin\\Desktop\\Dev\\reaper-reapy-mcp` with the actual path to your project folder.

After adding the configuration:
1. Restart Cursor
2. The MCP server will be available in your Cursor environment
3. You can use all the routing, track management, and other tools directly in Cursor

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
