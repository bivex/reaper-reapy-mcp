from mcp import types
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any, List, Union
import reapy
import logging
from src.utils.position_utils import position_to_time, time_to_measure

# Setup logger
logger = logging.getLogger(__name__)

# Constants to replace magic numbers
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_VELOCITY = 96
MAX_MIDI_PITCH = 127
MIN_MIDI_PITCH = 0

def _create_success_response(message: str) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {"status": "success", "message": message}

def _create_error_response(message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {"status": "error", "message": message}

def _handle_controller_operation(operation_name: str, operation_func, *args, **kwargs) -> Dict[str, Any]:
    """Generic handler for controller operations with proper error handling."""
    try:
        result = operation_func(*args, **kwargs)
        if result is not None and result is not False:
            return _create_success_response(f"{operation_name} completed successfully")
        return _create_error_response(f"Failed to {operation_name.lower()}")
    except Exception as e:
        logger.error(f"Controller operation failed: {operation_name} - {str(e)}")
        return _create_error_response(f"Failed to {operation_name.lower()}: {str(e)}")

def _setup_connection_tools(mcp: FastMCP, controller) -> None:
    """Setup connection-related MCP tools."""
    
    @mcp.tool("test_connection")
    def test_connection(ctx: Context) -> Dict[str, Any]:
        """Test connection to Reaper."""
        return _handle_controller_operation("Connection test", controller.verify_connection)

def _setup_track_tools(mcp: FastMCP, controller) -> None:
    """Setup track-related MCP tools."""
    
    @mcp.tool("create_track")
    def create_track(ctx: Context, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new track in Reaper."""
        try:
            track_index = controller.create_track(name)
            return _create_success_response(f"Created track {track_index}")
        except Exception as e:
            logger.error(f"Failed to create track: {str(e)}")
            return _create_error_response(f"Failed to create track: {str(e)}")

    @mcp.tool("rename_track")
    def rename_track(ctx: Context, track_index: int, new_name: str) -> Dict[str, Any]:
        """Rename an existing track."""
        operation_message = (
            f"Rename track {track_index} to {new_name}"
        )
        return _handle_controller_operation(
            operation_message,
            controller.rename_track, track_index, new_name
        )

    @mcp.tool("set_track_color")
    def set_track_color(ctx: Context, track_index: int, color: str) -> Dict[str, Any]:
        """Set the color of a track."""
        operation_message = (
            f"Set color of track {track_index} to {color}"
        )
        return _handle_controller_operation(
            operation_message,
            controller.set_track_color, track_index, color
        )

    @mcp.tool("get_track_color")
    def get_track_color(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the color of a track."""
        try:
            color = controller.get_track_color(track_index)
            return _create_success_response(f"Color of track {track_index}: {color}")
        except Exception as e:
            logger.error(f"Failed to get track color: {str(e)}")
            return _create_error_response(f"Failed to get track color: {str(e)}")

    @mcp.tool("get_track_count")
    def get_track_count(ctx: Context) -> Dict[str, Any]:
        """Get the number of tracks in the project."""
        try:
            count = controller.get_track_count()
            return _create_success_response(f"Track count: {count}")
        except Exception as e:
            logger.error(f"Failed to get track count: {str(e)}")
            return _create_error_response(f"Failed to get track count: {str(e)}")

def _setup_project_tools(mcp: FastMCP, controller) -> None:
    """Setup project-related MCP tools."""
    
    @mcp.tool("set_tempo")
    def set_tempo(ctx: Context, bpm: float) -> Dict[str, Any]:
        """Set the project tempo."""
        return _handle_controller_operation(
            f"Set tempo to {bpm} BPM",
            controller.set_tempo, bpm
        )

    @mcp.tool("get_tempo")
    def get_tempo(ctx: Context) -> Dict[str, Any]:
        """Get the current project tempo."""
        try:
            tempo = controller.get_tempo()
            return _create_success_response(f"Current tempo: {tempo} BPM")
        except Exception as e:
            logger.error(f"Failed to get tempo: {str(e)}")
            return _create_error_response(f"Failed to get tempo: {str(e)}")

    @mcp.tool("clear_project")
    def clear_project(ctx: Context) -> Dict[str, Any]:
        """Clear all items from all tracks in the project."""
        return _handle_controller_operation(
            "Clear all items from project",
            controller.clear_project
        )

def _setup_fx_tools(mcp: FastMCP, controller) -> None:
    """Setup FX-related MCP tools."""
    _setup_fx_add_remove_tools(mcp, controller)
    _setup_fx_param_tools(mcp, controller)
    _setup_fx_list_tools(mcp, controller)
    _setup_fx_toggle_tool(mcp, controller)

def _setup_fx_add_remove_tools(mcp: FastMCP, controller) -> None:
    """Setup FX add and remove MCP tools."""
    @mcp.tool("add_fx")
    def add_fx(ctx: Context, track_index: int, fx_name: str) -> Dict[str, Any]:
        """Add an FX to a track."""
        try:
            fx_index = controller.add_fx(track_index, fx_name)
            if fx_index >= 0:
                return _create_success_response(
                    f"Added FX {fx_name} to track {track_index} "
                    f"at index {fx_index}"
                )
            return _create_error_response(f"Failed to add FX to track {track_index}")
        except Exception as e:
            logger.error(f"Failed to add FX: {str(e)}")
            return _create_error_response(f"Failed to add FX: {str(e)}")

    @mcp.tool("remove_fx")
    def remove_fx(ctx: Context, track_index: int, fx_index: int) -> Dict[str, Any]:
        """Remove an FX from a track."""
        return _handle_controller_operation(
            f"Remove FX {fx_index} from track {track_index}",
            controller.remove_fx, track_index, fx_index
        )

def _setup_fx_param_tools(mcp: FastMCP, controller) -> None:
    """Setup FX parameter-related MCP tools."""
    @mcp.tool("set_fx_param")
    def set_fx_param(ctx: Context, track_index: int, fx_index: int, 
                    param_name: str, value: float) -> Dict[str, Any]:
        """Set an FX parameter value."""
        return _handle_controller_operation(
            f"Set FX parameter {param_name} to {value}",
            controller.set_fx_param, track_index, fx_index, param_name, value
        )

    @mcp.tool("get_fx_param")
    def get_fx_param(ctx: Context, track_index: int, fx_index: int, 
                    param_name: str) -> Dict[str, Any]:
        """Get an FX parameter value."""
        try:
            value = controller.get_fx_param(track_index, fx_index, param_name)
            return _create_success_response(f"FX parameter {param_name}: {value}")
        except Exception as e:
            logger.error(f"Failed to get FX parameter: {str(e)}")
            return _create_error_response(f"Failed to get FX parameter: {str(e)}")

    @mcp.tool("get_fx_param_list")
    def get_fx_param_list(ctx: Context, track_index: int, fx_index: int) -> Dict[str, Any]:
        """Get list of FX parameters."""
        try:
            params = controller.get_fx_param_list(track_index, fx_index)
            return _create_success_response(f"FX parameters: {params}")
        except Exception as e:
            logger.error(f"Failed to get FX parameters: {str(e)}")
            return _create_error_response(f"Failed to get FX parameters: {str(e)}")

def _setup_fx_list_tools(mcp: FastMCP, controller) -> None:
    """Setup FX list-related MCP tools."""
    @mcp.tool("get_fx_list")
    def get_fx_list(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get list of FX on a track."""
        try:
            fx_list = controller.get_fx_list(track_index)
            return _create_success_response(f"FX list for track {track_index}: {fx_list}")
        except Exception as e:
            logger.error(f"Failed to get FX list: {str(e)}")
            return _create_error_response(f"Failed to get FX list: {str(e)}")

    @mcp.tool("get_available_fx_list")
    def get_available_fx_list(ctx: Context) -> Dict[str, Any]:
        """Get list of available FX."""
        try:
            fx_list = controller.get_available_fx_list()
            return _create_success_response(f"Available FX: {fx_list}")
        except Exception as e:
            logger.error(f"Failed to get available FX: {str(e)}")
            return _create_error_response(f"Failed to get available FX: {str(e)}")

def _setup_fx_toggle_tool(mcp: FastMCP, controller) -> None:
    """Setup FX toggle MCP tool."""
    @mcp.tool("toggle_fx")
    def toggle_fx(ctx: Context, track_index: int, fx_index: int, 
                 enable: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle FX on/off."""
        action = "enable" if enable else "toggle"
        operation_name = f"{action.capitalize()} FX {fx_index} on track {track_index}"
        return _handle_controller_operation(
            operation_name,
            controller.toggle_fx, track_index, fx_index, enable
        )

def _setup_marker_tools(mcp: FastMCP, controller) -> None:
    """Setup marker and region-related MCP tools."""
    
    @mcp.tool("create_region")
    def create_region(ctx: Context, start_time: float, end_time: float, 
                     name: str) -> Dict[str, Any]:
        """Create a region in the project."""
        operation_name = f"Create region '{name}' from {start_time} to {end_time}"
        return _handle_controller_operation(
            operation_name,
            controller.create_region, start_time, end_time, name
        )

    @mcp.tool("delete_region")
    def delete_region(ctx: Context, region_index: int) -> Dict[str, Any]:
        """Delete a region from the project."""
        return _handle_controller_operation(
            f"Delete region {region_index}",
            controller.delete_region, region_index
        )

    @mcp.tool("create_marker")
    def create_marker(ctx: Context, time: float, name: str) -> Dict[str, Any]:
        """Create a marker at the specified time."""
        return _handle_controller_operation(
            f"Create marker '{name}' at {time}",
            controller.create_marker, time, name
        )

    @mcp.tool("delete_marker")
    def delete_marker(ctx: Context, marker_index: int) -> Dict[str, Any]:
        """Delete a marker from the project."""
        return _handle_controller_operation(
            f"Delete marker {marker_index}",
            controller.delete_marker, marker_index
        )

def _setup_master_tools(mcp: FastMCP, controller) -> None:
    """Setup master track-related MCP tools."""
    
    @mcp.tool("get_master_track")
    def get_master_track(ctx: Context) -> Dict[str, Any]:
        """Get master track information."""
        try:
            master_info = controller.get_master_track()
            return _create_success_response(f"Master track info: {master_info}")
        except Exception as e:
            logger.error(f"Failed to get master track: {str(e)}")
            return _create_error_response(f"Failed to get master track: {str(e)}")

    @mcp.tool("set_master_volume")
    def set_master_volume(ctx: Context, volume: float) -> Dict[str, Any]:
        """Set master track volume."""
        return _handle_controller_operation(
            f"Set master volume to {volume}",
            controller.set_master_volume, volume
        )

    @mcp.tool("set_master_pan")
    def set_master_pan(ctx: Context, pan: float) -> Dict[str, Any]:
        """Set master track pan."""
        return _handle_controller_operation(
            f"Set master pan to {pan}",
            controller.set_master_pan, pan
        )

    @mcp.tool("toggle_master_mute")
    def toggle_master_mute(ctx: Context, mute: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track mute."""
        action = "mute" if mute else "toggle mute"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.toggle_master_mute, mute
        )

    @mcp.tool("toggle_master_solo")
    def toggle_master_solo(ctx: Context, solo: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track solo."""
        action = "solo" if solo else "toggle solo"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.toggle_master_solo, solo
        )

def _setup_midi_tools(mcp: FastMCP, controller) -> None:
    """Setup MIDI-related MCP tools."""
    
    @mcp.tool("create_midi_item")
    def create_midi_item(ctx: Context, track_index: int, 
                        start_time: Optional[float] = None,
                        start_measure: Optional[str] = None, 
                        length: float = DEFAULT_MIDI_LENGTH) -> Dict[str, Any]:
        """Create a MIDI item."""
        try:
            # Handle time conversion if measure is provided
            if start_measure:
                start_time = time_to_measure(start_measure)
            
            item_id = controller.create_midi_item(track_index, start_time, length)
            return _create_success_response(f"Created MIDI item {item_id} on track {track_index}")
        except Exception as e:
            error_message = f"Failed to create MIDI item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("add_midi_note")
    def add_midi_note(ctx: Context, track_index: int, item_id: int, pitch: int,
                     start_time: float, length: float, 
                     velocity: int = DEFAULT_MIDI_VELOCITY) -> Dict[str, Any]:
        """Add a MIDI note to a MIDI item."""
        try:
            from src.controllers.midi.midi_controller import MIDIController
            note_params = MIDIController.MIDINoteParams(
                pitch=pitch,
                start_time=start_time,
                length=length,
                velocity=velocity
            )
            success = controller.add_midi_note(track_index, item_id, note_params)
            if success:
                return _create_success_response(f"Added MIDI note pitch {pitch} to item {item_id}")
            return _create_error_response(f"Failed to add MIDI note pitch {pitch} to item {item_id}")
        except Exception as e:
            logger.error(f"Failed to add MIDI note: {str(e)}")
            return _create_error_response(f"Failed to add MIDI note: {str(e)}")

    @mcp.tool("clear_midi_item")
    def clear_midi_item(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Clear all MIDI notes from a MIDI item."""
        return _handle_controller_operation(
            f"Clear MIDI item {item_id} on track {track_index}",
            controller.clear_midi_item, track_index, item_id
        )

    @mcp.tool("get_midi_notes")
    def get_midi_notes(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Get all MIDI notes from a MIDI item."""
        try:
            notes = controller.get_midi_notes(track_index, item_id)
            return _create_success_response(f"MIDI notes in item {item_id}: {notes}")
        except Exception as e:
            logger.error(f"Failed to get MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to get MIDI notes: {str(e)}")

    @mcp.tool("find_midi_notes_by_pitch")
    def find_midi_notes_by_pitch(ctx: Context, pitch_min: int = MIN_MIDI_PITCH, 
                                pitch_max: int = MAX_MIDI_PITCH) -> Dict[str, Any]:
        """Find MIDI notes within a pitch range."""
        try:
            notes = controller.find_midi_notes_by_pitch(pitch_min, pitch_max)
            return _create_success_response(f"MIDI notes in pitch range {pitch_min}-{pitch_max}: {notes}")
        except Exception as e:
            logger.error(f"Failed to find MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to find MIDI notes: {str(e)}")

    @mcp.tool("get_selected_midi_item")
    def get_selected_midi_item(ctx: Context) -> Dict[str, Any]:
        """Get the currently selected MIDI item."""
        try:
            item_info = controller.get_selected_midi_item()
            return _create_success_response(f"Selected MIDI item: {item_info}")
        except Exception as e:
            logger.error(f"Failed to get selected MIDI item: {str(e)}")
            return _create_error_response(f"Failed to get selected MIDI item: {str(e)}")

def _setup_audio_tools(mcp: FastMCP, controller) -> None:
    """Setup audio-related MCP tools."""
    _setup_audio_item_tools(mcp, controller)
    _setup_item_property_tools(mcp, controller)
    _setup_item_selection_tools(mcp, controller)


def _setup_audio_item_tools(mcp: FastMCP, controller) -> None:
    """Setup audio item creation and manipulation tools."""
    
    @mcp.tool("insert_audio_item")
    def insert_audio_item(ctx: Context, track_index: int, file_path: str,
                         start_time: Optional[float] = None, 
                         start_measure: Optional[str] = None) -> Dict[str, Any]:
        """Insert an audio file as an item on a track."""
        try:
            # Handle time conversion if measure is provided
            if start_measure:
                start_time = time_to_measure(start_measure)
            
            item_id = controller.insert_audio_item(track_index, file_path, start_time, start_measure)
            return _create_success_response(
                f"Inserted audio item {item_id} on track {track_index}"
            )
        except Exception as e:
            error_message = f"Failed to insert audio item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("duplicate_item")
    def duplicate_item(ctx: Context, track_index: int, item_id: int,
                      new_time: Optional[float] = None, 
                      new_measure: Optional[str] = None) -> Dict[str, Any]:
        """Duplicate an existing item."""
        try:
            # Handle time conversion if measure is provided
            if new_measure:
                new_time = time_to_measure(new_measure)
            
            new_item_id = controller.duplicate_item(track_index, item_id, new_time)
            return _create_success_response(
                f"Duplicated item {item_id} to {new_item_id}"
            )
        except Exception as e:
            error_message = f"Failed to duplicate item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("delete_item")
    def delete_item(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Delete an item from a track."""
        return _handle_controller_operation(
            f"Delete item {item_id} from track {track_index}",
            controller.delete_item, track_index, item_id
        )


def _setup_item_property_tools(mcp: FastMCP, controller) -> None:
    """Setup item property manipulation tools."""
    
    @mcp.tool("get_item_properties")
    def get_item_properties(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Get properties of an item."""
        try:
            properties = controller.get_item_properties(track_index, item_id)
            return _create_success_response(f"Item {item_id} properties: {properties}")
        except Exception as e:
            logger.error(f"Failed to get item properties: {str(e)}")
            return _create_error_response(f"Failed to get item properties: {str(e)}")

    @mcp.tool("set_item_position")
    def set_item_position(ctx: Context, track_index: int, item_id: int,
                         position_time: Optional[float] = None, 
                         position_measure: Optional[str] = None) -> Dict[str, Any]:
        """Set the position of an item."""
        try:
            # Handle time conversion if measure is provided
            if position_measure:
                position_time = time_to_measure(position_measure)
            
            success = controller.set_item_position(track_index, item_id, position_time)
            if success:
                return _create_success_response(f"Set position of item {item_id}")
            return _create_error_response(f"Failed to set item position")
        except Exception as e:
            logger.error(f"Failed to set item position: {str(e)}")
            return _create_error_response(f"Failed to set item position: {str(e)}")

    @mcp.tool("set_item_length")
    def set_item_length(ctx: Context, track_index: int, item_id: int, 
                       length: float) -> Dict[str, Any]:
        """Set the length of an item."""
        return _handle_controller_operation(
            f"Set length of item {item_id} to {length}",
            controller.set_item_length, track_index, item_id, length
        )


def _setup_item_selection_tools(mcp: FastMCP, controller) -> None:
    """Setup item selection and query tools."""
    
    @mcp.tool("get_items_in_time_range")
    def get_items_in_time_range(ctx: Context, track_index: int,
                               start_time: Optional[float] = None, 
                               end_time: Optional[float] = None,
                               start_measure: Optional[str] = None, 
                               end_measure: Optional[str] = None) -> Dict[str, Any]:
        """Get items within a time range."""
        try:
            # Handle time conversion if measures are provided
            if start_measure:
                start_time = time_to_measure(start_measure)
            if end_measure:
                end_time = time_to_measure(end_measure)
            
            items = controller.get_items_in_time_range(track_index, start_time, end_time)
            return _create_success_response(f"Items in time range: {items}")
        except Exception as e:
            logger.error(f"Failed to get items in time range: {str(e)}")
            return _create_error_response(f"Failed to get items in time range: {str(e)}")

    @mcp.tool("get_selected_items")
    def get_selected_items(ctx: Context) -> Dict[str, Any]:
        """Get all selected items."""
        try:
            items = controller.get_selected_items()
            return _create_success_response(f"Selected items: {items}")
        except Exception as e:
            logger.error(f"Failed to get selected items: {str(e)}")
            return _create_error_response(f"Failed to get selected items: {str(e)}")


def _setup_routing_tools(mcp: FastMCP, controller) -> None:
    """Setup routing-related MCP tools."""
    
    @mcp.tool("add_send")
    def add_send(ctx: Context, source_track: int, destination_track: int, 
                 volume: float = 0.0, pan: float = 0.0, 
                 mute: bool = False, phase: bool = False, 
                 channels: int = 2) -> Dict[str, Any]:
        """Add a send from source track to destination track."""
        try:
            send_id = controller.add_send(source_track, destination_track, volume, pan, mute, phase, channels)
            if send_id is not None:
                return _create_success_response(f"Added send from track {source_track} to track {destination_track} with ID {send_id}")
            return _create_error_response(f"Failed to add send from track {source_track} to track {destination_track}")
        except Exception as e:
            logger.error(f"Failed to add send: {str(e)}")
            return _create_error_response(f"Failed to add send: {str(e)}")

    @mcp.tool("remove_send")
    def remove_send(ctx: Context, source_track: int, send_id: int) -> Dict[str, Any]:
        """Remove a send from a track."""
        return _handle_controller_operation(
            f"Remove send {send_id} from track {source_track}",
            controller.remove_send, source_track, send_id
        )

    @mcp.tool("get_sends")
    def get_sends(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get all sends from a track."""
        try:
            sends = controller.get_sends(track_index)
            return _create_success_response(f"Sends for track {track_index}: {sends}")
        except Exception as e:
            logger.error(f"Failed to get sends: {str(e)}")
            return _create_error_response(f"Failed to get sends: {str(e)}")

    @mcp.tool("get_receives")
    def get_receives(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get all receives on a track."""
        try:
            receives = controller.get_receives(track_index)
            return _create_success_response(f"Receives for track {track_index}: {receives}")
        except Exception as e:
            logger.error(f"Failed to get receives: {str(e)}")
            return _create_error_response(f"Failed to get receives: {str(e)}")

    @mcp.tool("set_send_volume")
    def set_send_volume(ctx: Context, source_track: int, send_id: int, volume: float) -> Dict[str, Any]:
        """Set the volume of a send."""
        return _handle_controller_operation(
            f"Set send {send_id} volume to {volume} dB",
            controller.set_send_volume, source_track, send_id, volume
        )

    @mcp.tool("set_send_pan")
    def set_send_pan(ctx: Context, source_track: int, send_id: int, pan: float) -> Dict[str, Any]:
        """Set the pan of a send."""
        return _handle_controller_operation(
            f"Set send {send_id} pan to {pan}",
            controller.set_send_pan, source_track, send_id, pan
        )

    @mcp.tool("toggle_send_mute")
    def toggle_send_mute(ctx: Context, source_track: int, send_id: int, mute: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle or set the mute state of a send."""
        try:
            success = controller.toggle_send_mute(source_track, send_id, mute)
            if success:
                action = "toggled" if mute is None else f"set to {mute}"
                return _create_success_response(f"Send {send_id} mute {action}")
            return _create_error_response(f"Failed to toggle send {send_id} mute")
        except Exception as e:
            logger.error(f"Failed to toggle send mute: {str(e)}")
            return _create_error_response(f"Failed to toggle send mute: {str(e)}")

    @mcp.tool("get_track_routing_info")
    def get_track_routing_info(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get comprehensive routing information for a track."""
        try:
            routing_info = controller.get_track_routing_info(track_index)
            return _create_success_response(f"Routing info for track {track_index}: {routing_info}")
        except Exception as e:
            logger.error(f"Failed to get track routing info: {str(e)}")
            return _create_error_response(f"Failed to get track routing info: {str(e)}")

    @mcp.tool("debug_track_routing")
    def debug_track_routing(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Debug track routing information for troubleshooting."""
        try:
            debug_info = controller.debug_track_routing(track_index)
            return _create_success_response(f"Debug info for track {track_index}: {debug_info}")
        except Exception as e:
            logger.error(f"Failed to debug track routing: {str(e)}")
            return _create_error_response(f"Failed to debug track routing: {str(e)}")

    @mcp.tool("clear_all_sends")
    def clear_all_sends(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Remove all sends from a track."""
        return _handle_controller_operation(
            f"Clear all sends from track {track_index}",
            controller.clear_all_sends, track_index
        )

    @mcp.tool("clear_all_receives")
    def clear_all_receives(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Remove all receives from a track."""
        return _handle_controller_operation(
            f"Clear all receives from track {track_index}",
            controller.clear_all_receives, track_index
        )


def _setup_advanced_routing_tools(mcp: FastMCP, controller) -> None:
    """Setup advanced routing and bussing MCP tools."""
    
    @mcp.tool("create_folder_track")
    def create_folder_track(ctx: Context, name: str = "Folder Track") -> Dict[str, Any]:
        """Create a folder track that can contain other tracks."""
        return _handle_controller_operation(
            f"Create folder track '{name}'",
            controller.create_folder_track, name
        )

    @mcp.tool("create_bus_track")
    def create_bus_track(ctx: Context, name: str = "Bus Track") -> Dict[str, Any]:
        """Create a bus track for grouping and processing multiple tracks."""
        return _handle_controller_operation(
            f"Create bus track '{name}'",
            controller.create_bus_track, name
        )

    @mcp.tool("set_track_parent")
    def set_track_parent(ctx: Context, child_track_index: int, parent_track_index: int) -> Dict[str, Any]:
        """Set a track's parent folder track."""
        return _handle_controller_operation(
            f"Set track {child_track_index} as child of track {parent_track_index}",
            controller.set_track_parent, child_track_index, parent_track_index
        )

    @mcp.tool("get_track_children")
    def get_track_children(ctx: Context, parent_track_index: int) -> Dict[str, Any]:
        """Get all child tracks of a parent track."""
        try:
            children = controller.get_track_children(parent_track_index)
            return _create_success_response(f"Children of track {parent_track_index}: {children}")
        except Exception as e:
            logger.error(f"Failed to get track children: {str(e)}")
            return _create_error_response(f"Failed to get track children: {str(e)}")

    @mcp.tool("set_track_folder_depth")
    def set_track_folder_depth(ctx: Context, track_index: int, depth: int) -> Dict[str, Any]:
        """Set the folder depth of a track."""
        return _handle_controller_operation(
            f"Set track {track_index} folder depth to {depth}",
            controller.set_track_folder_depth, track_index, depth
        )

    @mcp.tool("get_track_folder_depth")
    def get_track_folder_depth(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the folder depth of a track."""
        try:
            depth = controller.get_track_folder_depth(track_index)
            return _create_success_response(f"Track {track_index} folder depth: {depth}")
        except Exception as e:
            logger.error(f"Failed to get track folder depth: {str(e)}")
            return _create_error_response(f"Failed to get track folder depth: {str(e)}")


def _setup_automation_tools(mcp: FastMCP, controller) -> None:
    """Setup automation and modulation MCP tools."""
    
    @mcp.tool("create_automation_envelope")
    def create_automation_envelope(ctx: Context, track_index: int, envelope_name: str) -> Dict[str, Any]:
        """Create an automation envelope on a track."""
        return _handle_controller_operation(
            f"Create automation envelope '{envelope_name}' on track {track_index}",
            controller.create_automation_envelope, track_index, envelope_name
        )

    @mcp.tool("add_automation_point")
    def add_automation_point(ctx: Context, track_index: int, envelope_name: str, time: float, value: float, shape: int = 0) -> Dict[str, Any]:
        """Add an automation point to an envelope."""
        return _handle_controller_operation(
            f"Add automation point at {time}s with value {value} on track {track_index}",
            controller.add_automation_point, track_index, envelope_name, time, value, shape
        )

    @mcp.tool("get_automation_points")
    def get_automation_points(ctx: Context, track_index: int, envelope_name: str) -> Dict[str, Any]:
        """Get all automation points from an envelope."""
        try:
            points = controller.get_automation_points(track_index, envelope_name)
            return _create_success_response(f"Automation points for '{envelope_name}' on track {track_index}: {points}")
        except Exception as e:
            logger.error(f"Failed to get automation points: {str(e)}")
            return _create_error_response(f"Failed to get automation points: {str(e)}")

    @mcp.tool("set_automation_mode")
    def set_automation_mode(ctx: Context, track_index: int, mode: str) -> Dict[str, Any]:
        """Set the automation mode for a track."""
        return _handle_controller_operation(
            f"Set automation mode to '{mode}' on track {track_index}",
            controller.set_automation_mode, track_index, mode
        )

    @mcp.tool("get_automation_mode")
    def get_automation_mode(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the current automation mode for a track."""
        try:
            mode = controller.get_automation_mode(track_index)
            return _create_success_response(f"Track {track_index} automation mode: {mode}")
        except Exception as e:
            logger.error(f"Failed to get automation mode: {str(e)}")
            return _create_error_response(f"Failed to get automation mode: {str(e)}")

    @mcp.tool("delete_automation_point")
    def delete_automation_point(ctx: Context, track_index: int, envelope_name: str, point_index: int) -> Dict[str, Any]:
        """Delete an automation point from an envelope."""
        return _handle_controller_operation(
            f"Delete automation point {point_index} from '{envelope_name}' on track {track_index}",
            controller.delete_automation_point, track_index, envelope_name, point_index
        )


def _setup_advanced_item_tools(mcp: FastMCP, controller) -> None:
    """Setup advanced item operations MCP tools."""
    
    @mcp.tool("split_item")
    def split_item(ctx: Context, track_index: int, item_index: int, split_time: float) -> Dict[str, Any]:
        """Split an item at a specific time."""
        try:
            new_items = controller.split_item(track_index, item_index, split_time)
            return _create_success_response(f"Split item {item_index} at {split_time}s, created {len(new_items)} new items: {new_items}")
        except Exception as e:
            logger.error(f"Failed to split item: {str(e)}")
            return _create_error_response(f"Failed to split item: {str(e)}")

    @mcp.tool("glue_items")
    def glue_items(ctx: Context, track_index: int, item_indices: List[int]) -> Dict[str, Any]:
        """Glue multiple items together into a single item."""
        return _handle_controller_operation(
            f"Glue {len(item_indices)} items on track {track_index}",
            controller.glue_items, track_index, item_indices
        )

    @mcp.tool("fade_in")
    def fade_in(ctx: Context, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> Dict[str, Any]:
        """Add a fade-in to an item."""
        return _handle_controller_operation(
            f"Add {fade_length}s fade-in to item {item_index} on track {track_index}",
            controller.fade_in, track_index, item_index, fade_length, fade_curve
        )

    @mcp.tool("fade_out")
    def fade_out(ctx: Context, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> Dict[str, Any]:
        """Add a fade-out to an item."""
        return _handle_controller_operation(
            f"Add {fade_length}s fade-out to item {item_index} on track {track_index}",
            controller.fade_out, track_index, item_index, fade_length, fade_curve
        )

    @mcp.tool("crossfade_items")
    def crossfade_items(ctx: Context, track_index: int, item1_index: int, item2_index: int, crossfade_length: float) -> Dict[str, Any]:
        """Create a crossfade between two items."""
        return _handle_controller_operation(
            f"Create {crossfade_length}s crossfade between items {item1_index} and {item2_index}",
            controller.crossfade_items, track_index, item1_index, item2_index, crossfade_length
        )



    @mcp.tool("reverse_item")
    def reverse_item(ctx: Context, track_index: int, item_index: int) -> Dict[str, Any]:
        """Reverse an item."""
        return _handle_controller_operation(
            f"Reverse item {item_index} on track {track_index}",
            controller.reverse_item, track_index, item_index
        )

    @mcp.tool("get_item_fade_info")
    def get_item_fade_info(ctx: Context, track_index: int, item_index: int) -> Dict[str, Any]:
        """Get fade information for an item."""
        try:
            fade_info = controller.get_item_fade_info(track_index, item_index)
            return _create_success_response(f"Fade info for item {item_index} on track {track_index}: {fade_info}")
        except Exception as e:
            logger.error(f"Failed to get item fade info: {str(e)}")
            return _create_error_response(f"Failed to get item fade info: {str(e)}")


def setup_mcp_tools(mcp: FastMCP, controller) -> None:
    """Setup MCP tools for Reaper control."""
    _setup_connection_tools(mcp, controller)
    _setup_track_tools(mcp, controller)
    _setup_project_tools(mcp, controller)
    _setup_fx_tools(mcp, controller)
    _setup_marker_tools(mcp, controller)
    _setup_master_tools(mcp, controller)
    _setup_midi_tools(mcp, controller)
    _setup_audio_tools(mcp, controller)
    _setup_routing_tools(mcp, controller)
    _setup_advanced_routing_tools(mcp, controller)
    _setup_automation_tools(mcp, controller)
    _setup_advanced_item_tools(mcp, controller)
