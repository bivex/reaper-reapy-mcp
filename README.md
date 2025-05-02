# Reaper and MCP or AI integration

A Python application for controlling REAPER Digital Audio Workstation (DAW) using the MCP(Model context protocol).

## Features

- Track management (create, rename, color)
- FX management (add, remove, parameter control)
- Project tempo control
- Region and marker management
- Master track control
- MCP (Message Control Protocol) integration for remote control

## Requirements

- Python 3.7+
- REAPER DAW
- `python-reapy` Python module
- `mcp[cli]` package for MCP server

## Installation

1. Install REAPER if you haven't already
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Enable python in REAPER:
4. Enable reapy server via REAPER scripting
   ```python
   import reapy
   reapy.config.enable_dist_api()
   ```

### MCP Integration

The application includes MCP tools for remote control. To use them:

1. Start the MCP server:
   ```bash
   python src/run_mcp_server.py
   ```

2. Use the MCP inspector to test the tools:
   ```bash
   test_mcp.bat
   ```

Available MCP tools:
- `test_connection`: Verify connection to REAPER
- `create_track`: Create a new track
- `rename_track`: Rename an existing track
- `set_tempo`: Set project tempo
- `get_tempo`: Get current tempo
- `set_track_color`: Set track color
- `get_track_color`: Get track color
- `add_fx`: Add an FX to a track
- `remove_fx`: Remove an FX from a track
- `set_fx_param`: Set FX parameter value
- `get_fx_param`: Get FX parameter value
- `toggle_fx`: Toggle FX enable/disable state
- `create_region`: Create a region
- `delete_region`: Delete a region
- `create_marker`: Create a marker
- `delete_marker`: Delete a marker
- `get_master_track`: Get master track information
- `set_master_volume`: Set master track volume
- `set_master_pan`: Set master track pan
- `toggle_master_mute`: Toggle master track mute
- `toggle_master_solo`: Toggle master track solo

Claude configuration:
```
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

## Error Handling

The controller includes comprehensive error handling and logging. When debug mode is enabled, detailed information about operations and any errors will be logged.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.