from mcp import types
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any

def setup_mcp_tools(mcp: FastMCP, controller) -> None:
    """Setup MCP tools for Reaper control."""
    
    @mcp.tool("test_connection")
    def test_connection(ctx: Context) -> Dict[str, Any]:
        """Test connection to Reaper."""
        try:
            if controller.verify_connection():
                return {"status": "success", "message": "Connected to Reaper"}
            return {"status": "error", "message": "Failed to connect to Reaper"}
        except Exception as e:
            return {"status": "error", "message": f"Connection test failed: {str(e)}"}

    @mcp.tool("create_track")
    def create_track(ctx: Context, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new track in Reaper."""
        try:
            track_index = controller.create_track(name)
            return {"status": "success", "message": f"Created track {track_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create track: {str(e)}"}

    @mcp.tool("rename_track")
    def rename_track(ctx: Context, track_index: int, new_name: str) -> Dict[str, Any]:
        """Rename an existing track."""
        try:
            if controller.rename_track(track_index, new_name):
                return {"status": "success", "message": f"Renamed track {track_index} to {new_name}"}
            return {"status": "error", "message": f"Failed to rename track {track_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to rename track: {str(e)}"}

    @mcp.tool("set_tempo")
    def set_tempo(ctx: Context, bpm: float) -> Dict[str, Any]:
        """Set the project tempo."""
        try:
            if controller.set_tempo(bpm):
                return {"status": "success", "message": f"Set tempo to {bpm} BPM"}
            return {"status": "error", "message": "Failed to set tempo"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to set tempo: {str(e)}"}

    @mcp.tool("get_tempo")
    def get_tempo(ctx: Context) -> Dict[str, Any]:
        """Get the current project tempo."""
        try:
            tempo = controller.get_tempo()
            return {"status": "success", "message": f"Current tempo: {tempo} BPM"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get tempo: {str(e)}"}

    @mcp.tool("set_track_color")
    def set_track_color(ctx: Context, track_index: int, color: str) -> Dict[str, Any]:
        """Set the color of a track."""
        try:
            if controller.set_track_color(track_index, color):
                return {"status": "success", "message": f"Set color of track {track_index} to {color}"}
            return {"status": "error", "message": f"Failed to set color for track {track_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to set track color: {str(e)}"}

    @mcp.tool("get_track_color")
    def get_track_color(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the color of a track."""
        try:
            color = controller.get_track_color(track_index)
            return {"status": "success", "message": f"Color of track {track_index}: {color}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get track color: {str(e)}"}

    @mcp.tool("add_fx")
    def add_fx(ctx: Context, track_index: int, fx_name: str) -> Dict[str, Any]:
        """Add an FX to a track."""
        try:
            fx_index = controller.add_fx(track_index, fx_name)
            if fx_index >= 0:
                return {"status": "success", "message": f"Added FX {fx_name} to track {track_index} at index {fx_index}"}
            return {"status": "error", "message": f"Failed to add FX to track {track_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to add FX: {str(e)}"}

    @mcp.tool("remove_fx")
    def remove_fx(ctx: Context, track_index: int, fx_index: int) -> Dict[str, Any]:
        """Remove an FX from a track."""
        try:
            if controller.remove_fx(track_index, fx_index):
                return {"status": "success", "message": f"Removed FX {fx_index} from track {track_index}"}
            return {"status": "error", "message": f"Failed to remove FX from track {track_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to remove FX: {str(e)}"}

    @mcp.tool("set_fx_param")
    def set_fx_param(ctx: Context, track_index: int, fx_index: int, param_name: str, value: float) -> Dict[str, Any]:
        """Set an FX parameter value."""
        try:
            if controller.set_fx_param(track_index, fx_index, param_name, value):
                return {"status": "success", "message": f"Set parameter {param_name} to {value} for FX {fx_index} on track {track_index}"}
            return {"status": "error", "message": "Failed to set FX parameter"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to set FX parameter: {str(e)}"}

    @mcp.tool("get_fx_param")
    def get_fx_param(ctx: Context, track_index: int, fx_index: int, param_name: str) -> Dict[str, Any]:
        """Get an FX parameter value."""
        try:
            value = controller.get_fx_param(track_index, fx_index, param_name)
            return {"status": "success", "message": f"Parameter {param_name} value: {value}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get FX parameter: {str(e)}"}

    @mcp.tool("toggle_fx")
    def toggle_fx(ctx: Context, track_index: int, fx_index: int, enable: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle or set the enable/disable state of an FX."""
        try:
            if controller.toggle_fx(track_index, fx_index, enable):
                state = "enabled" if enable else "disabled" if enable is not None else "toggled"
                return {"status": "success", "message": f"{state} FX {fx_index} on track {track_index}"}
            return {"status": "error", "message": "Failed to toggle FX"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to toggle FX: {str(e)}"}

    @mcp.tool("create_region")
    def create_region(ctx: Context, start_time: float, end_time: float, name: str) -> Dict[str, Any]:
        """Create a region in the project."""
        try:
            region_index = controller.create_region(start_time, end_time, name)
            if region_index >= 0:
                return {"status": "success", "message": f"Created region {region_index}: {name}"}
            return {"status": "error", "message": "Failed to create region"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create region: {str(e)}"}

    @mcp.tool("delete_region")
    def delete_region(ctx: Context, region_index: int) -> Dict[str, Any]:
        """Delete a region from the project."""
        try:
            if controller.delete_region(region_index):
                return {"status": "success", "message": f"Deleted region {region_index}"}
            return {"status": "error", "message": f"Failed to delete region {region_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete region: {str(e)}"}

    @mcp.tool("create_marker")
    def create_marker(ctx: Context, time: float, name: str) -> Dict[str, Any]:
        """Create a marker in the project."""
        try:
            marker_index = controller.create_marker(time, name)
            if marker_index >= 0:
                return {"status": "success", "message": f"Created marker {marker_index}: {name}"}
            return {"status": "error", "message": "Failed to create marker"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create marker: {str(e)}"}

    @mcp.tool("delete_marker")
    def delete_marker(ctx: Context, marker_index: int) -> Dict[str, Any]:
        """Delete a marker from the project."""
        try:
            if controller.delete_marker(marker_index):
                return {"status": "success", "message": f"Deleted marker {marker_index}"}
            return {"status": "error", "message": f"Failed to delete marker {marker_index}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete marker: {str(e)}"}

    @mcp.tool("get_master_track")
    def get_master_track(ctx: Context) -> Dict[str, Any]:
        """Get information about the master track."""
        try:
            info = controller.get_master_track()
            return {"status": "success", "message": f"Master track info: {info}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get master track info: {str(e)}"}

    @mcp.tool("set_master_volume")
    def set_master_volume(ctx: Context, volume: float) -> Dict[str, Any]:
        """Set the master track volume."""
        try:
            if controller.set_master_volume(volume):
                return {"status": "success", "message": f"Set master volume to {volume}"}
            return {"status": "error", "message": "Failed to set master volume"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to set master volume: {str(e)}"}

    @mcp.tool("set_master_pan")
    def set_master_pan(ctx: Context, pan: float) -> Dict[str, Any]:
        """Set the master track pan."""
        try:
            if controller.set_master_pan(pan):
                return {"status": "success", "message": f"Set master pan to {pan}"}
            return {"status": "error", "message": "Failed to set master pan"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to set master pan: {str(e)}"}

    @mcp.tool("toggle_master_mute")
    def toggle_master_mute(ctx: Context, mute: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle or set the master track mute state."""
        try:
            if controller.toggle_master_mute(mute):
                state = "muted" if mute else "unmuted" if mute is not None else "toggled"
                return {"status": "success", "message": f"Master track {state}"}
            return {"status": "error", "message": "Failed to toggle master mute"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to toggle master mute: {str(e)}"}

    @mcp.tool("toggle_master_solo")
    def toggle_master_solo(ctx: Context, solo: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle or set the master track solo state."""
        try:
            if controller.toggle_master_solo(solo):
                state = "soloed" if solo else "unsoloed" if solo is not None else "toggled"
                return {"status": "success", "message": f"Master track {state}"}
            return {"status": "error", "message": "Failed to toggle master solo"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to toggle master solo: {str(e)}"} 