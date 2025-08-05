# Reaper and MCP or AI integration

A Python application for controlling REAPER Digital Audio Workstation (DAW) using the MCP(Model context protocol).

![REAPER MCP Demo](docs/media/reaper-reapy-mcp-demo-for-gif-002.gif)

## Features

- **Track Management**: Create, rename, and color tracks
- **FX Management**: Add, remove, and control effect parameters
- **Project Control**: Set tempo, manage regions and markers, clear all items
- **Master Track Control**: Volume, pan, mute, and solo operations
- **MIDI Operations**: Create items, add/get notes, clear items with musical positioning
- **Audio Item Operations**: Insert, duplicate, modify with enhanced positioning support
- **Routing Management**: Create, manage, and control track sends and receives
- **Advanced Routing & Bussing**: Folder tracks, bus tracks, parent-child relationships
- **Automation & Modulation**: Create envelopes, add points, manage automation modes
- **Advanced Item Operations**: Split, glue, fade, crossfade, reverse items
- **Dual Position Format**: Support both time (seconds) and measure:beat notation
- **Reliable Duplication**: Uses REAPER's built-in commands for accurate item copying
- **MCP Integration**: Model Context Protocol server for AI assistant control

## Requirements

- Python 3.10+
- REAPER DAW
- `python-reapy` Python module
- `mcp[cli]` package for MCP server
- Internet connection (for downloading sample audio file)

## Installation

1. Install REAPER if you haven't already
2. Install the project dependencies in system Python:
   ```bash
   pip install -e .
   ```
3. Enable reapy server:
   - Make sure REAPER is running
   - Run from command line (not from REAPER):
   ```bash
   python reaper_side_enable_server.py
   ```
   **Note**: This must be run from system Python, not from REAPER's built-in Python, because REAPER uses Python 3.4 which doesn't have the reapy module.
4. Test the MCP server connection

## Quick Start

### Option 1: Windows (Recommended)
1. Make sure REAPER is running
2. Double-click `start_mcp_server.bat`
3. The server will start and show connection status

### Option 2: Command Line
1. Make sure REAPER is running
2. Run the server:
   ```bash
   uv run -m src.run_mcp_server
   ```

### Option 3: Manual Python
1. Make sure REAPER is running
2. Run:
   ```bash
   python -m src.run_mcp_server
   ```

## Troubleshooting Connection Issues

If you get connection errors like `ConnectionRefusedError`, follow these steps:

### Step 1: Configure REAPER Port
**Important**: First, check what port REAPER is actually listening on:
1. Open Task Manager > Details tab
2. Look for `reaper.exe` in the list
3. Check the "Local Port" column - this shows the actual port REAPER is using

**Configure the correct port**:
1. Open `start_reapy_server_simple.py` in a text editor
2. Change the port number in line 5 to match what you see in Task Manager:
   ```python
   RPR_SetExtState("reapy", "server_port", "2307", 1)  # Change 2307 to your actual port
   ```
3. Save the file

### Step 2: Enable REAPER Remote API
In REAPER:
1. Go to Actions > Show action list
2. Search for "reapy"
3. Run "reapy: Enable remote API"
4. **Restart REAPER** for changes to take effect

### Step 3: Alternative - Manual Configuration
If the above doesn't work:
1. In REAPER, go to Preferences > Plug-ins > ReaScript
2. Enable "Allow TCP connections"
3. Set port to match what you see in Task Manager
4. Restart REAPER

### Step 4: Test Connection
Run the test script:
```bash
python start_reapy_server_simple.py
```

You should see: "✅ Connection established successfully!"

### Common Port Issues
- **Default port**: 2306
- **Common alternative**: 2307
- **Check actual port**: Use Task Manager to see what port REAPER is actually using
- **Port mismatch**: If the port in your script doesn't match REAPER's actual port, connection will fail

## Running the Server

You can run the server using uv directly:
```bash
uv --directory <project_path> run -m src.run_mcp_server
```

For example, on Windows:
```bash
uv --directory C:\path\to\reaper-reapy-mcp run -m src.run_mcp_server
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

### Advanced Routing & Bussing
| Tool | Description | Parameters |
|------|-------------|------------|
| `create_folder_track` | Create a folder track that can contain other tracks | `name` |
| `create_bus_track` | Create a bus track for grouping and processing multiple tracks | `name` |
| `set_track_parent` | Set a track's parent folder track | `child_track_index`, `parent_track_index` |
| `get_track_children` | Get all child tracks of a parent track | `parent_track_index` |
| `set_track_folder_depth` | Set the folder depth of a track | `track_index`, `depth` |
| `get_track_folder_depth` | Get the folder depth of a track | `track_index` |

### Automation & Modulation
| Tool | Description | Parameters |
|------|-------------|------------|
| `create_automation_envelope` | Create an automation envelope on a track | `track_index`, `envelope_name` |
| `add_automation_point` | Add an automation point to an envelope | `track_index`, `envelope_name`, `time`, `value`, `shape` |
| `get_automation_points` | Get all automation points from an envelope | `track_index`, `envelope_name` |
| `set_automation_mode` | Set the automation mode for a track | `track_index`, `mode` |
| `get_automation_mode` | Get the current automation mode for a track | `track_index` |
| `delete_automation_point` | Delete an automation point from an envelope | `track_index`, `envelope_name`, `point_index` |

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
| `clear_project` | Clear all items from all tracks in the project |
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

**Note**: The `get_items_in_time_range` function now properly handles optional time parameters and supports both time and measure:beat formats. The `insert_audio_item` function has been fixed to handle None values for start_time properly.

### Advanced Item Operations
| Tool | Description | Parameters |
|------|-------------|------------|
| `split_item` | Split an item at a specific time | `track_index`, `item_index`, `split_time` |
| `glue_items` | Glue multiple items together into a single item | `track_index`, `item_indices` |
| `fade_in` | Add a fade-in to an item | `track_index`, `item_index`, `fade_length`, `fade_curve` |
| `fade_out` | Add a fade-out to an item | `track_index`, `item_index`, `fade_length`, `fade_curve` |
| `crossfade_items` | Create a crossfade between two items | `track_index`, `item1_index`, `item2_index`, `crossfade_length` |
| `reverse_item` | Reverse an item | `track_index`, `item_index` |
| `get_item_fade_info` | Get fade information for an item | `track_index`, `item_index` |

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

### Advanced Routing Examples

#### Folder and Bus Track Creation
```python
# Create a folder track for drums
create_folder_track("Drums")

# Create a bus track for effects
create_bus_track("FX Bus")

# Set track 1 as child of the drums folder
set_track_parent(child_track_index=1, parent_track_index=0)

# Get all children of the drums folder
get_track_children(parent_track_index=0)
```

### Automation Examples

#### Creating and Managing Automation
```python
# Create a volume automation envelope
create_automation_envelope(track_index=0, envelope_name="volume")

# Add automation points
add_automation_point(track_index=0, envelope_name="volume", time=0.0, value=0.0)
add_automation_point(track_index=0, envelope_name="volume", time=2.0, value=1.0)
add_automation_point(track_index=0, envelope_name="volume", time=4.0, value=0.5)

# Set automation mode to write
set_automation_mode(track_index=0, mode="write")

# Get all automation points
get_automation_points(track_index=0, envelope_name="volume")
```

### Advanced Item Operations Examples

#### Item Editing and Processing
```python
# Split an item at 2 seconds
split_item(track_index=0, item_index=0, split_time=2.0)

# Add fade-in to an item
fade_in(track_index=0, item_index=0, fade_length=0.5, fade_curve=0)

# Add fade-out to an item
fade_out(track_index=0, item_index=1, fade_length=1.0, fade_curve=2)

# Create crossfade between two items
crossfade_items(track_index=0, item1_index=0, item2_index=1, crossfade_length=0.5)

# Reverse an item
reverse_item(track_index=0, item_index=0)

# Glue multiple items together
glue_items(track_index=0, item_indices=[0, 1, 2])

# Clear all items from the entire project
clear_project()
```

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
