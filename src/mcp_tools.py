from mcp import types
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any, List, Union
import logging
from src.time.conversion import (
    parse_position,
    measure_beat_to_time,
    time_to_measure_beat,
)

# Use centralized reapy bridge
from src.core.reapy_bridge import get_reapy

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


def _handle_controller_operation(
    operation_name: str, operation_func, *args, **kwargs
) -> Dict[str, Any]:
    """Generic handler for controller operations with proper error handling."""
    try:
        result = operation_func(*args, **kwargs)
        # Handle boolean results: True/False are explicit success/failure
        # Handle numeric results: >= 0 is success, < 0 is failure
        # Handle None: generally failure unless operation is expected to return None
        if result is True or (isinstance(result, (int, float)) and result >= 0):
            return _create_success_response(f"{operation_name} completed successfully")
        elif result is False or (isinstance(result, (int, float)) and result < 0):
            return _create_error_response(f"Failed to {operation_name.lower()}")
        elif (
            result is not None
        ):  # Non-boolean, non-numeric success (strings, objects, etc.)
            return _create_success_response(f"{operation_name} completed successfully")
        else:  # result is None
            return _create_error_response(f"Failed to {operation_name.lower()}")
    except Exception as e:
        logger.error(f"Controller operation failed: {operation_name} - {str(e)}")
        return _create_error_response(f"Failed to {operation_name.lower()}: {str(e)}")


def _setup_connection_tools(mcp: FastMCP, controller) -> None:
    """Setup connection-related MCP tools."""

    @mcp.tool("test_connection")
    def test_connection(ctx: Context) -> Dict[str, Any]:
        """Test connection to Reaper."""
        return _handle_controller_operation(
            "Connection test", controller.verify_connection
        )


def _setup_track_tools(mcp: FastMCP, controller) -> None:
    """Setup track-related MCP tools."""

    @mcp.tool("create_track")
    def create_track(ctx: Context, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new track in Reaper."""
        try:
            track_index = controller.track.create_track(name)
            return _create_success_response(f"Created track {track_index}")
        except Exception as e:
            logger.error(f"Failed to create track: {str(e)}")
            return _create_error_response(f"Failed to create track: {str(e)}")

    @mcp.tool("rename_track")
    def rename_track(ctx: Context, track_index: int, new_name: str) -> Dict[str, Any]:
        """Rename an existing track."""
        operation_message = f"Rename track {track_index} to {new_name}"
        return _handle_controller_operation(
            operation_message, controller.track.rename_track, track_index, new_name
        )

    @mcp.tool("set_track_color")
    def set_track_color(ctx: Context, track_index: int, color: str) -> Dict[str, Any]:
        """Set the color of a track."""
        operation_message = f"Set color of track {track_index} to {color}"
        return _handle_controller_operation(
            operation_message, controller.track.set_track_color, track_index, color
        )

    @mcp.tool("get_track_color")
    def get_track_color(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the color of a track."""
        try:
            color = controller.track.get_track_color(track_index)
            return _create_success_response(f"Color of track {track_index}: {color}")
        except Exception as e:
            logger.error(f"Failed to get track color: {str(e)}")
            return _create_error_response(f"Failed to get track color: {str(e)}")

    @mcp.tool("get_track_count")
    def get_track_count(ctx: Context) -> Dict[str, Any]:
        """Get the number of tracks in the project."""
        try:
            count = controller.track.get_track_count()
            return _create_success_response(f"Track count: {count}")
        except Exception as e:
            logger.error(f"Failed to get track count: {str(e)}")
            return _create_error_response(f"Failed to get track count: {str(e)}")

    @mcp.tool("set_track_volume")
    def set_track_volume(
        ctx: Context, track_index: int, volume_db: float
    ) -> Dict[str, Any]:
        """
        Set the volume of a track in dB.

        Args:
            track_index (int): Index of the track
            volume_db (float): Volume in dB (typical range: -inf to +12dB)
        """
        return _handle_controller_operation(
            f"Set track {track_index} volume to {volume_db} dB",
            controller.track.set_track_volume,
            track_index,
            volume_db,
        )

    @mcp.tool("get_track_volume")
    def get_track_volume(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the volume of a track in dB."""
        try:
            volume = controller.track.get_track_volume(track_index)
            return _create_success_response(
                f"Track {track_index} volume: {volume:.2f} dB"
            )
        except Exception as e:
            logger.error(f"Failed to get track volume: {str(e)}")
            return _create_error_response(f"Failed to get track volume: {str(e)}")

    @mcp.tool("set_track_pan")
    def set_track_pan(ctx: Context, track_index: int, pan: float) -> Dict[str, Any]:
        """
        Set the pan position of a track.

        Args:
            track_index (int): Index of the track
            pan (float): Pan position (-1.0 = hard left, 0.0 = center, 1.0 = hard right)
        """
        return _handle_controller_operation(
            f"Set track {track_index} pan to {pan}",
            controller.track.set_track_pan,
            track_index,
            pan,
        )

    @mcp.tool("get_track_pan")
    def get_track_pan(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the pan position of a track."""
        try:
            pan = controller.track.get_track_pan(track_index)
            return _create_success_response(f"Track {track_index} pan: {pan}")
        except Exception as e:
            logger.error(f"Failed to get track pan: {str(e)}")
            return _create_error_response(f"Failed to get track pan: {str(e)}")

    @mcp.tool("set_track_mute")
    def set_track_mute(ctx: Context, track_index: int, mute: bool) -> Dict[str, Any]:
        """
        Set the mute state of a track.

        Args:
            track_index (int): Index of the track
            mute (bool): True to mute, False to unmute
        """
        return _handle_controller_operation(
            f"Set track {track_index} mute to {mute}",
            controller.track.set_track_mute,
            track_index,
            mute,
        )

    @mcp.tool("get_track_mute")
    def get_track_mute(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the mute state of a track."""
        try:
            mute = controller.track.get_track_mute(track_index)
            return _create_success_response(f"Track {track_index} mute: {mute}")
        except Exception as e:
            logger.error(f"Failed to get track mute: {str(e)}")
            return _create_error_response(f"Failed to get track mute: {str(e)}")

    @mcp.tool("set_track_solo")
    def set_track_solo(ctx: Context, track_index: int, solo: bool) -> Dict[str, Any]:
        """
        Set the solo state of a track.

        Args:
            track_index (int): Index of the track
            solo (bool): True to solo, False to unsolo
        """
        return _handle_controller_operation(
            f"Set track {track_index} solo to {solo}",
            controller.track.set_track_solo,
            track_index,
            solo,
        )

    @mcp.tool("get_track_solo")
    def get_track_solo(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the solo state of a track."""
        try:
            solo = controller.track.get_track_solo(track_index)
            return _create_success_response(f"Track {track_index} solo: {solo}")
        except Exception as e:
            logger.error(f"Failed to get track solo: {str(e)}")
            return _create_error_response(f"Failed to get track solo: {str(e)}")

    @mcp.tool("toggle_track_mute")
    def toggle_track_mute(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Toggle the mute state of a track."""
        return _handle_controller_operation(
            f"Toggle track {track_index} mute",
            controller.track.toggle_track_mute,
            track_index,
        )

    @mcp.tool("toggle_track_solo")
    def toggle_track_solo(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Toggle the solo state of a track."""
        return _handle_controller_operation(
            f"Toggle track {track_index} solo",
            controller.track.toggle_track_solo,
            track_index,
        )

    @mcp.tool("set_track_arm")
    def set_track_arm(ctx: Context, track_index: int, arm: bool) -> Dict[str, Any]:
        """
        Set the record arm state of a track.

        Args:
            track_index (int): Index of the track
            arm (bool): True to arm for recording, False to disarm
        """
        return _handle_controller_operation(
            f"Set track {track_index} record arm to {arm}",
            controller.track.set_track_arm,
            track_index,
            arm,
        )

    @mcp.tool("get_track_arm")
    def get_track_arm(ctx: Context, track_index: int) -> Dict[str, Any]:
        """Get the record arm state of a track."""
        try:
            arm = controller.track.get_track_arm(track_index)
            return _create_success_response(f"Track {track_index} record arm: {arm}")
        except Exception as e:
            logger.error(f"Failed to get track record arm: {str(e)}")
            return _create_error_response(f"Failed to get track record arm: {str(e)}")


def _setup_project_tools(mcp: FastMCP, controller) -> None:
    """Setup project-related MCP tools."""

    @mcp.tool("set_tempo")
    def set_tempo(ctx: Context, bpm: float) -> Dict[str, Any]:
        """Set the project tempo."""
        return _handle_controller_operation(
            f"Set tempo to {bpm} BPM", controller.project.set_tempo, bpm
        )

    @mcp.tool("get_tempo")
    def get_tempo(ctx: Context) -> Dict[str, Any]:
        """Get the current project tempo."""
        try:
            tempo = controller.project.get_tempo()
            return _create_success_response(f"Current tempo: {tempo} BPM")
        except Exception as e:
            logger.error(f"Failed to get tempo: {str(e)}")
            return _create_error_response(f"Failed to get tempo: {str(e)}")

    @mcp.tool("clear_project")
    def clear_project(ctx: Context) -> Dict[str, Any]:
        """Clear all items from all tracks in the project."""
        return _handle_controller_operation(
            "Clear all items from project", controller.project.clear_project
        )


def _setup_fx_tools(mcp: FastMCP, controller) -> None:
    """Setup FX-related MCP tools."""
    _setup_fx_add_remove_tools(mcp, controller)
    _setup_fx_param_tools(mcp, controller)
    _setup_fx_list_tools(mcp, controller)
    _setup_fx_toggle_tool(mcp, controller)
    _setup_dynamics_tools(mcp, controller)
    _setup_meter_tools(mcp, controller)


def _setup_fx_add_remove_tools(mcp: FastMCP, controller) -> None:
    """Setup FX add and remove MCP tools."""

    @mcp.tool("add_fx")
    def add_fx(ctx: Context, track_index: int, fx_name: str) -> Dict[str, Any]:
        """Add an FX to a track."""
        try:
            fx_index = controller.fx.add_fx(track_index, fx_name)
            if fx_index >= 0:
                return _create_success_response(
                    f"Added FX {fx_name} to track {track_index} " f"at index {fx_index}"
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
            controller.fx.remove_fx,
            track_index,
            fx_index,
        )


def _setup_fx_param_tools(mcp: FastMCP, controller) -> None:
    """Setup FX parameter-related MCP tools."""

    @mcp.tool("set_fx_param")
    def set_fx_param(
        ctx: Context, track_index: int, fx_index: int, param_name: str, value: float
    ) -> Dict[str, Any]:
        """
        Set an FX parameter value.

        Args:
            track_index (int): Index of the track containing the FX
            fx_index (int): Index of the FX on the track
            param_name (str): Name of the parameter to set
            value (float): Parameter value (use number, not string)
        """
        return _handle_controller_operation(
            f"Set FX parameter {param_name} to {value}",
            controller.fx.set_fx_param,
            track_index,
            fx_index,
            param_name,
            value,
        )

    @mcp.tool("get_fx_param")
    def get_fx_param(
        ctx: Context, track_index: int, fx_index: int, param_name: str
    ) -> Dict[str, Any]:
        """Get an FX parameter value."""
        try:
            value = controller.fx.get_fx_param(track_index, fx_index, param_name)
            return _create_success_response(f"FX parameter {param_name}: {value}")
        except Exception as e:
            logger.error(f"Failed to get FX parameter: {str(e)}")
            return _create_error_response(f"Failed to get FX parameter: {str(e)}")

    @mcp.tool("get_fx_param_list")
    def get_fx_param_list(
        ctx: Context, track_index: int, fx_index: int
    ) -> Dict[str, Any]:
        """Get list of FX parameters.

        Note: Some FX like ReaEQ may have limited parameter enumeration.
        For better parameter testing, try ReaComp or ReaLimit instead.
        """
        try:
            params = controller.fx.get_fx_param_list(track_index, fx_index)
            if not params:
                # Provide helpful message if no parameters found
                fx_list = controller.fx.get_fx_list(track_index)
                fx_name = (
                    fx_list[fx_index]["name"] if fx_index < len(fx_list) else "Unknown"
                )
                return _create_success_response(
                    f"No parameters found for FX '{fx_name}'. Try ReaComp or ReaLimit for better parameter enumeration."
                )
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
            fx_list = controller.fx.get_fx_list(track_index)
            return _create_success_response(
                f"FX list for track {track_index}: {fx_list}"
            )
        except Exception as e:
            logger.error(f"Failed to get FX list: {str(e)}")
            return _create_error_response(f"Failed to get FX list: {str(e)}")

    @mcp.tool("get_available_fx_list")
    def get_available_fx_list(ctx: Context) -> Dict[str, Any]:
        """Get list of available FX.

        Note: For testing FX parameters, ReaComp and ReaLimit typically work better
        than ReaEQ for parameter enumeration.
        """
        try:
            fx_list = controller.fx.get_available_fx_list()
            return _create_success_response(f"Available FX: {fx_list}")
        except Exception as e:
            logger.error(f"Failed to get available FX: {str(e)}")
            return _create_error_response(f"Failed to get available FX: {str(e)}")


def _setup_fx_toggle_tool(mcp: FastMCP, controller) -> None:
    """Setup FX toggle MCP tool."""

    @mcp.tool("toggle_fx")
    def toggle_fx(
        ctx: Context, track_index: int, fx_index: int, enable: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Toggle FX on/off."""
        try:
            result = controller.fx.toggle_fx(track_index, fx_index, enable)
            action = (
                "enabled"
                if enable is True
                else "disabled" if enable is False else "toggled"
            )
            if result:
                return _create_success_response(
                    f"FX {fx_index} on track {track_index} {action} successfully"
                )
            else:
                return _create_error_response(
                    f"Failed to toggle FX {fx_index} on track {track_index}"
                )
        except Exception as e:
            logger.error(f"Toggle FX operation failed: {str(e)}")
            return _create_error_response(
                f"Failed to toggle FX {fx_index} on track {track_index}: {str(e)}"
            )


def _setup_dynamics_tools(mcp: FastMCP, controller) -> None:
    """Setup dynamics processing MCP tools."""

    @mcp.tool("set_compressor_params")
    def set_compressor_params(
        ctx: Context,
        track_index: int,
        fx_index: int,
        threshold: Optional[float] = None,
        ratio: Optional[float] = None,
        attack: Optional[float] = None,
        release: Optional[float] = None,
        makeup_gain: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Set common compressor parameters.

        Args:
            track_index (int): Index of the track containing the compressor
            fx_index (int): Index of the compressor FX on the track
            threshold (float, optional): Threshold in dB (typical range: -60 to 0)
            ratio (float, optional): Compression ratio (typical range: 1.0 to 20.0)
            attack (float, optional): Attack time in ms (typical range: 0.1 to 100)
            release (float, optional): Release time in ms (typical range: 10 to 1000)
            makeup_gain (float, optional): Makeup gain in dB (typical range: 0 to 20)
        """
        return _handle_controller_operation(
            f"Set compressor parameters on track {track_index} FX {fx_index}",
            controller.fx.set_compressor_params,
            track_index,
            fx_index,
            threshold,
            ratio,
            attack,
            release,
            makeup_gain,
        )

    @mcp.tool("set_limiter_params")
    def set_limiter_params(
        ctx: Context,
        track_index: int,
        fx_index: int,
        threshold: Optional[float] = None,
        ceiling: Optional[float] = None,
        release: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Set common limiter parameters.

        Args:
            track_index (int): Index of the track containing the limiter
            fx_index (int): Index of the limiter FX on the track
            threshold (float, optional): Threshold in dB (typical range: -20 to 0)
            ceiling (float, optional): Output ceiling in dB (typical range: -10 to 0)
            release (float, optional): Release time in ms (typical range: 1 to 100)
        """
        return _handle_controller_operation(
            f"Set limiter parameters on track {track_index} FX {fx_index}",
            controller.fx.set_limiter_params,
            track_index,
            fx_index,
            threshold,
            ceiling,
            release,
        )


def _setup_meter_tools(mcp: FastMCP, controller) -> None:
    """Setup meter reading MCP tools."""

    @mcp.tool("get_track_peak_level")
    def get_track_peak_level(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get the current peak levels for a track.

        Args:
            track_index (int): Index of the track to get peak levels from
        """
        try:
            peak_levels = controller.fx.get_track_peak_level(track_index)
            return _create_success_response(
                f"Track {track_index} peak levels: {peak_levels}"
            )
        except Exception as e:
            logger.error(f"Failed to get track peak level: {str(e)}")
            return _create_error_response(f"Failed to get track peak level: {str(e)}")

    @mcp.tool("get_master_peak_level")
    def get_master_peak_level(ctx: Context) -> Dict[str, Any]:
        """Get the current peak levels for the master track."""
        try:
            peak_levels = controller.fx.get_master_peak_level()
            return _create_success_response(f"Master peak levels: {peak_levels}")
        except Exception as e:
            logger.error(f"Failed to get master peak level: {str(e)}")
            return _create_error_response(f"Failed to get master peak level: {str(e)}")


def _setup_marker_tools(mcp: FastMCP, controller) -> None:
    """Setup marker and region-related MCP tools."""

    @mcp.tool("create_region")
    def create_region(
        ctx: Context, start_time: float, end_time: float, name: str
    ) -> Dict[str, Any]:
        """
        Create a region in the project.

        Args:
            start_time (float): Start time in seconds (use number, not string)
            end_time (float): End time in seconds (use number, not string)
            name (str): Name of the region
        """
        operation_name = f"Create region '{name}' from {start_time} to {end_time}"
        return _handle_controller_operation(
            operation_name, controller.marker.create_region, start_time, end_time, name
        )

    @mcp.tool("delete_region")
    def delete_region(ctx: Context, region_index: int) -> Dict[str, Any]:
        """Delete a region from the project."""
        return _handle_controller_operation(
            f"Delete region {region_index}",
            controller.marker.delete_region,
            region_index,
        )

    @mcp.tool("create_marker")
    def create_marker(ctx: Context, time: float, name: str) -> Dict[str, Any]:
        """
        Create a marker at the specified time.

        Args:
            time (float): Time in seconds (use number, not string)
            name (str): Name of the marker
        """
        return _handle_controller_operation(
            f"Create marker '{name}' at {time}",
            controller.marker.create_marker,
            time,
            name,
        )

    @mcp.tool("delete_marker")
    def delete_marker(ctx: Context, marker_index: int) -> Dict[str, Any]:
        """Delete a marker from the project."""
        return _handle_controller_operation(
            f"Delete marker {marker_index}",
            controller.marker.delete_marker,
            marker_index,
        )


def _setup_master_tools(mcp: FastMCP, controller) -> None:
    """Setup master track-related MCP tools."""

    @mcp.tool("get_master_track")
    def get_master_track(ctx: Context) -> Dict[str, Any]:
        """Get master track information."""
        try:
            master_info = controller.master.get_master_track()
            return _create_success_response(f"Master track info: {master_info}")
        except Exception as e:
            logger.error(f"Failed to get master track: {str(e)}")
            return _create_error_response(f"Failed to get master track: {str(e)}")

    @mcp.tool("set_master_volume")
    def set_master_volume(ctx: Context, volume: float) -> Dict[str, Any]:
        """
        Set master track volume.

        Args:
            volume (float): Volume in dB (use number, not string, e.g., -6.0, 0.0, 3.0)
        """
        return _handle_controller_operation(
            f"Set master volume to {volume}",
            controller.master.set_master_volume,
            volume,
        )

    @mcp.tool("set_master_pan")
    def set_master_pan(ctx: Context, pan: float) -> Dict[str, Any]:
        """
        Set master track pan.

        Args:
            pan (float): Pan position (-1.0 to 1.0, use number, not string)
        """
        return _handle_controller_operation(
            f"Set master pan to {pan}", controller.master.set_master_pan, pan
        )

    @mcp.tool("toggle_master_mute")
    def toggle_master_mute(ctx: Context, mute: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track mute."""
        action = "mute" if mute else "toggle mute"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.master.toggle_master_mute,
            mute,
        )

    @mcp.tool("toggle_master_solo")
    def toggle_master_solo(ctx: Context, solo: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle master track solo."""
        action = "solo" if solo else "toggle solo"
        return _handle_controller_operation(
            f"{action.capitalize()} master track",
            controller.master.toggle_master_solo,
            solo,
        )


def _setup_midi_tools(mcp: FastMCP, controller) -> None:
    """Setup MIDI-related MCP tools."""

    @mcp.tool("create_midi_item")
    def create_midi_item(
        ctx: Context,
        track_index: int,
        start_time: Optional[float] = None,
        start_measure: Optional[str] = None,
        length: float = DEFAULT_MIDI_LENGTH,
    ) -> Dict[str, Any]:
        """
        Create a MIDI item.

        Args:
            track_index (int): Index of the track to create MIDI item on
            start_time (float, optional): Start time in seconds (use number, not string)
            start_measure (str, optional): Start measure (e.g., "1.1.0")
            length (float): Length of the MIDI item in seconds (use number, not string)
        """
        try:
            # Handle time conversion if measure is provided
            if start_measure:
                start_time = parse_position(start_measure)

            # Use 0.0 as default start time if none provided
            if start_time is None:
                start_time = 0.0

            item_id = controller.midi.create_midi_item(track_index, start_time, length)
            if item_id is not None and item_id >= 0:
                return _create_success_response(
                    f"Created MIDI item {item_id} on track {track_index}"
                )
            else:
                return _create_error_response(
                    f"Failed to create MIDI item on track {track_index}"
                )
        except Exception as e:
            error_message = f"Failed to create MIDI item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("add_midi_note")
    def add_midi_note(
        ctx: Context,
        track_index: int,
        item_id: int,
        pitch: int,
        start_time: float,
        length: float,
        velocity: int = DEFAULT_MIDI_VELOCITY,
    ) -> Dict[str, Any]:
        """
        Add a MIDI note to a MIDI item.

        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int): ID of the MIDI item
            pitch (int): MIDI pitch (0-127)
            start_time (float): Start time in seconds (use number, not string)
            length (float): Note length in seconds (use number, not string)
            velocity (int): Note velocity (0-127)
        """
        try:
            from src.controllers.midi.midi_controller import MIDIController

            note_params = MIDIController.MIDINoteParams(
                pitch=pitch, start_time=start_time, length=length, velocity=velocity
            )
            success = controller.midi.add_midi_note(track_index, item_id, note_params)
            if success:
                return _create_success_response(
                    f"Added MIDI note pitch {pitch} to item {item_id}"
                )
            return _create_error_response(
                f"Failed to add MIDI note pitch {pitch} to item {item_id}"
            )
        except Exception as e:
            logger.error(f"Failed to add MIDI note: {str(e)}")
            return _create_error_response(f"Failed to add MIDI note: {str(e)}")

    @mcp.tool("clear_midi_item")
    def clear_midi_item(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Clear all MIDI notes from a MIDI item."""
        return _handle_controller_operation(
            f"Clear MIDI item {item_id} on track {track_index}",
            controller.midi.clear_midi_item,
            track_index,
            item_id,
        )

    @mcp.tool("get_midi_notes")
    def get_midi_notes(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Get all MIDI notes from a MIDI item."""
        try:
            notes = controller.midi.get_midi_notes(track_index, item_id)
            return _create_success_response(f"MIDI notes in item {item_id}: {notes}")
        except Exception as e:
            logger.error(f"Failed to get MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to get MIDI notes: {str(e)}")

    @mcp.tool("find_midi_notes_by_pitch")
    def find_midi_notes_by_pitch(
        ctx: Context, pitch_min: int = MIN_MIDI_PITCH, pitch_max: int = MAX_MIDI_PITCH
    ) -> Dict[str, Any]:
        """Find MIDI notes within a pitch range."""
        try:
            notes = controller.midi.find_midi_notes_by_pitch(pitch_min, pitch_max)
            return _create_success_response(
                f"MIDI notes in pitch range {pitch_min}-{pitch_max}: {notes}"
            )
        except Exception as e:
            logger.error(f"Failed to find MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to find MIDI notes: {str(e)}")

    @mcp.tool("get_selected_midi_item")
    def get_selected_midi_item(ctx: Context) -> Dict[str, Any]:
        """Get the currently selected MIDI item."""
        try:
            item_info = controller.midi.get_selected_midi_item()
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
    def insert_audio_item(
        ctx: Context,
        track_index: int,
        file_path: str,
        start_time: Optional[float] = None,
        start_measure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Insert an audio file as an item on a track.

        Args:
            track_index (int): Index of the track to insert audio item on
            file_path (str): Path to the audio file
            start_time (float, optional): Start time in seconds (use number, not string)
            start_measure (str, optional): Start measure (e.g., "1.1.0")
        """
        try:
            # Handle time conversion if measure is provided
            if start_measure:
                start_time = parse_position(start_measure)

            item_id = controller.audio.insert_audio_item(
                track_index, file_path, start_time, start_measure
            )
            if item_id is None:
                return _create_error_response(
                    f"Failed to insert audio item on track {track_index}"
                )
            return _create_success_response(
                f"Inserted audio item {item_id} on track {track_index}"
            )
        except Exception as e:
            error_message = f"Failed to insert audio item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("create_blank_item")
    def create_blank_item(
        ctx: Context,
        track_index: int,
        start_time: float,
        length: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Create a blank media item on a track.

        Args:
            track_index (int): Destination track index
            start_time (float): Start time in seconds
            length (float): Item length in seconds (min 0.1s)
        """
        try:
            new_index = controller.audio.create_blank_item_on_track(
                track_index, start_time, length
            )
            if isinstance(new_index, int) and new_index >= 0:
                return _create_success_response(
                    f"Created blank item at index {new_index} on track {track_index}"
                )
            return _create_error_response(
                f"Failed to create blank item on track {track_index}"
            )
        except Exception as e:
            logger.error(f"Failed to create blank item: {str(e)}")
            return _create_error_response(f"Failed to create blank item: {str(e)}")

    @mcp.tool("duplicate_item")
    def duplicate_item(
        ctx: Context,
        track_index: int,
        item_id: int,
        new_time: Optional[float] = None,
        new_measure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Duplicate an existing item.

        Args:
            track_index (int): Index of the track containing the item
            item_id (int): ID of the item to duplicate
            new_time (float, optional): New position in seconds (use number, not string)
            new_measure (str, optional): New position as measure (e.g., "2.1.0")
        """
        try:
            # Handle time conversion if measure is provided
            if new_measure:
                new_time = parse_position(new_measure)

            new_item_id = controller.audio.duplicate_item(
                track_index, item_id, new_time
            )
            if new_item_id is not None and new_item_id != -1:
                return _create_success_response(
                    f"Duplicated item {item_id} to {new_item_id}"
                )
            else:
                return _create_error_response(
                    f"Failed to duplicate item {item_id} on track {track_index}"
                )
        except Exception as e:
            error_message = f"Failed to duplicate item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("delete_item")
    def delete_item(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """
        Delete an item from a track.

        Args:
            track_index (int): Index of the track containing the item
            item_id (int): ID of the item to delete
        """
        return _handle_controller_operation(
            f"Delete item {item_id} from track {track_index}",
            controller.audio.delete_item,
            track_index,
            item_id,
        )


def _setup_item_property_tools(mcp: FastMCP, controller) -> None:
    """Setup item property manipulation tools."""

    @mcp.tool("get_item_properties")
    def get_item_properties(
        ctx: Context, track_index: int, item_id: int
    ) -> Dict[str, Any]:
        """
        Get properties of an item.

        Args:
            track_index (int): Index of the track containing the item
            item_id (int): ID of the item to get properties from
        """
        try:
            properties = controller.audio.get_item_properties(track_index, item_id)
            return _create_success_response(f"Item {item_id} properties: {properties}")
        except Exception as e:
            logger.error(f"Failed to get item properties: {str(e)}")
            return _create_error_response(f"Failed to get item properties: {str(e)}")

    @mcp.tool("set_item_position")
    def set_item_position(
        ctx: Context,
        track_index: int,
        item_id: int,
        position_time: Optional[float] = None,
        position_measure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Set the position of an item.

        Args:
            track_index (int): Index of the track containing the item
            item_id (int): ID of the item to reposition
            position_time (float, optional): New position in seconds (use number, not string)
            position_measure (str, optional): New position as measure (e.g., "2.1.0")
        """
        try:
            # Handle time conversion if measure is provided
            if position_measure:
                position_time = parse_position(position_measure)

            success = controller.audio.set_item_position(
                track_index, item_id, position_time
            )
            if success:
                return _create_success_response(f"Set position of item {item_id}")
            return _create_error_response(f"Failed to set item position")
        except Exception as e:
            logger.error(f"Failed to set item position: {str(e)}")
            return _create_error_response(f"Failed to set item position: {str(e)}")

    @mcp.tool("set_item_length")
    def set_item_length(
        ctx: Context, track_index: int, item_id: int, length: float
    ) -> Dict[str, Any]:
        """
        Set the length of an item.

        Args:
            track_index (int): Index of the track containing the item
            item_id (int): ID of the item to resize
            length (float): New length in seconds (use number, not string)
        """
        return _handle_controller_operation(
            f"Set length of item {item_id} to {length}",
            controller.audio.set_item_length,
            track_index,
            item_id,
            length,
        )


def _setup_item_selection_tools(mcp: FastMCP, controller) -> None:
    """Setup item selection and query tools."""

    @mcp.tool("get_items_in_time_range")
    def get_items_in_time_range(
        ctx: Context,
        track_index: int,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        start_measure: Optional[str] = None,
        end_measure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get items within a time range.

        Args:
            track_index (int): Index of the track to search
            start_time (float, optional): Start time in seconds (use number, not string)
            end_time (float, optional): End time in seconds (use number, not string)
            start_measure (str, optional): Start measure (e.g., "1.1.0")
            end_measure (str, optional): End measure (e.g., "4.1.0")
        """
        try:
            # Handle time conversion if measures are provided
            if start_measure:
                start_time = parse_position(start_measure)
            if end_measure:
                end_time = parse_position(end_measure)

            items = controller.audio.get_items_in_time_range(
                track_index, start_time, end_time
            )
            return _create_success_response(f"Items in time range: {items}")
        except Exception as e:
            logger.error(f"Failed to get items in time range: {str(e)}")
            return _create_error_response(
                f"Failed to get items in time range: {str(e)}"
            )

    @mcp.tool("get_selected_items")
    def get_selected_items(ctx: Context) -> Dict[str, Any]:
        """Get all selected items."""
        try:
            items = controller.audio.get_selected_items()
            return _create_success_response(f"Selected items: {items}")
        except Exception as e:
            logger.error(f"Failed to get selected items: {str(e)}")
            return _create_error_response(f"Failed to get selected items: {str(e)}")


def _setup_routing_tools(mcp: FastMCP, controller) -> None:
    """Setup routing-related MCP tools."""
    from constants import DEFAULT_STEREO_CHANNELS

    @mcp.tool("add_send")
    def add_send(
        ctx: Context,
        source_track: int,
        destination_track: int,
        volume: float = 0.0,
        pan: float = 0.0,
        mute: bool = False,
        phase: bool = False,
        channels: int = DEFAULT_STEREO_CHANNELS,
    ) -> Dict[str, Any]:
        """
        Add a send from source track to destination track.

        Args:
            source_track (int): Index of the source track
            destination_track (int): Index of the destination track
            volume (float): Send volume in dB (use number, not string, e.g., -6.0, 0.0)
            pan (float): Send pan position (-1.0 to 1.0, use number, not string)
            mute (bool): Whether the send is muted
            phase (bool): Whether phase is inverted
            channels (int): Number of channels (1 or 2)
        """
        try:
            send_id = controller.routing.add_send(
                source_track, destination_track, volume, pan, mute, phase, channels
            )
            if send_id is not None:
                return _create_success_response(
                    f"Added send from track {source_track} to track {destination_track} with ID {send_id}"
                )
            return _create_error_response(
                f"Failed to add send from track {source_track} to track {destination_track}"
            )
        except Exception as e:
            logger.error(f"Failed to add send: {str(e)}")
            return _create_error_response(f"Failed to add send: {str(e)}")

    @mcp.tool("remove_send")
    def remove_send(ctx: Context, source_track: int, send_id: int) -> Dict[str, Any]:
        """
        Remove a send from a track.

        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send to remove
        """
        return _handle_controller_operation(
            f"Remove send {send_id} from track {source_track}",
            controller.routing.remove_send,
            source_track,
            send_id,
        )

    @mcp.tool("get_sends")
    def get_sends(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get all sends from a track.

        Args:
            track_index (int): Index of the track to get sends from
        """
        try:
            sends = controller.routing.get_sends(track_index)
            return _create_success_response(f"Sends for track {track_index}: {sends}")
        except Exception as e:
            logger.error(f"Failed to get sends: {str(e)}")
            return _create_error_response(f"Failed to get sends: {str(e)}")

    @mcp.tool("get_receives")
    def get_receives(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get all receives on a track.

        Args:
            track_index (int): Index of the track to get receives from
        """
        try:
            receives = controller.routing.get_receives(track_index)
            return _create_success_response(
                f"Receives for track {track_index}: {receives}"
            )
        except Exception as e:
            logger.error(f"Failed to get receives: {str(e)}")
            return _create_error_response(f"Failed to get receives: {str(e)}")

    @mcp.tool("set_send_volume")
    def set_send_volume(
        ctx: Context, source_track: int, send_id: int, volume: float
    ) -> Dict[str, Any]:
        """
        Set the volume of a send.

        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send to set volume for
            volume (float): Send volume in dB (use number, not string, e.g., -6.0, 0.0)
        """
        return _handle_controller_operation(
            f"Set send {send_id} volume to {volume} dB",
            controller.routing.set_send_volume,
            source_track,
            send_id,
            volume,
        )

    @mcp.tool("set_send_pan")
    def set_send_pan(
        ctx: Context, source_track: int, send_id: int, pan: float
    ) -> Dict[str, Any]:
        """
        Set the pan of a send.

        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send to set pan for
            pan (float): Send pan position (-1.0 to 1.0, use number, not string)
        """
        return _handle_controller_operation(
            f"Set send {send_id} pan to {pan}",
            controller.routing.set_send_pan,
            source_track,
            send_id,
            pan,
        )

    @mcp.tool("toggle_send_mute")
    def toggle_send_mute(
        ctx: Context, source_track: int, send_id: int, mute: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Toggle or set the mute state of a send.

        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send to toggle mute for
            mute (bool, optional): If True, mute the send; if False, unmute; if None, toggle
        """
        try:
            success = controller.routing.toggle_send_mute(source_track, send_id, mute)
            if success:
                action = "toggled" if mute is None else f"set to {mute}"
                return _create_success_response(f"Send {send_id} mute {action}")
            return _create_error_response(f"Failed to toggle send {send_id} mute")
        except Exception as e:
            logger.error(f"Failed to toggle send mute: {str(e)}")
            return _create_error_response(f"Failed to toggle send mute: {str(e)}")

    @mcp.tool("get_track_routing_info")
    def get_track_routing_info(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get comprehensive routing information for a track.

        Args:
            track_index (int): Index of the track to get routing info for
        """
        try:
            routing_info = controller.routing.get_track_routing_info(track_index)
            return _create_success_response(
                f"Routing info for track {track_index}: {routing_info}"
            )
        except Exception as e:
            logger.error(f"Failed to get track routing info: {str(e)}")
            return _create_error_response(f"Failed to get track routing info: {str(e)}")

    @mcp.tool("debug_track_routing")
    def debug_track_routing(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Debug track routing information for troubleshooting.

        Args:
            track_index (int): Index of the track to debug routing for
        """
        try:
            debug_info = controller.routing.debug_track_routing(track_index)
            return _create_success_response(
                f"Debug info for track {track_index}: {debug_info}"
            )
        except Exception as e:
            logger.error(f"Failed to debug track routing: {str(e)}")
            return _create_error_response(f"Failed to debug track routing: {str(e)}")

    @mcp.tool("clear_all_sends")
    def clear_all_sends(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Remove all sends from a track.

        Args:
            track_index (int): Index of the track to clear sends from
        """
        return _handle_controller_operation(
            f"Clear all sends from track {track_index}",
            controller.routing.clear_all_sends,
            track_index,
        )

    @mcp.tool("clear_all_receives")
    def clear_all_receives(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Remove all receives from a track.

        Args:
            track_index (int): Index of the track to clear receives from
        """
        return _handle_controller_operation(
            f"Clear all receives from track {track_index}",
            controller.routing.clear_all_receives,
            track_index,
        )


def _setup_advanced_routing_tools(mcp: FastMCP, controller) -> None:
    """Setup advanced routing and bussing MCP tools."""

    @mcp.tool("create_folder_track")
    def create_folder_track(ctx: Context, name: str = "Folder Track") -> Dict[str, Any]:
        """
        Create a folder track that can contain other tracks.

        Args:
            name (str): Name for the folder track
        """
        return _handle_controller_operation(
            f"Create folder track '{name}'",
            controller.advanced_routing.create_folder_track,
            name,
        )

    @mcp.tool("create_bus_track")
    def create_bus_track(ctx: Context, name: str = "Bus Track") -> Dict[str, Any]:
        """
        Create a bus track for grouping and processing multiple tracks.

        Args:
            name (str): Name for the bus track
        """
        return _handle_controller_operation(
            f"Create bus track '{name}'",
            controller.advanced_routing.create_bus_track,
            name,
        )

    @mcp.tool("set_track_parent")
    def set_track_parent(
        ctx: Context, child_track_index: int, parent_track_index: int
    ) -> Dict[str, Any]:
        """
        Set a track's parent folder track.

        Args:
            child_track_index (int): Index of the child track
            parent_track_index (int): Index of the parent track
        """
        return _handle_controller_operation(
            f"Set track {child_track_index} as child of track {parent_track_index}",
            controller.advanced_routing.set_track_parent,
            child_track_index,
            parent_track_index,
        )

    @mcp.tool("get_track_children")
    def get_track_children(ctx: Context, parent_track_index: int) -> Dict[str, Any]:
        """
        Get all child tracks of a parent track.

        Args:
            parent_track_index (int): Index of the parent track
        """
        try:
            children = controller.advanced_routing.get_track_children(
                parent_track_index
            )
            return _create_success_response(
                f"Children of track {parent_track_index}: {children}"
            )
        except Exception as e:
            logger.error(f"Failed to get track children: {str(e)}")
            return _create_error_response(f"Failed to get track children: {str(e)}")

    @mcp.tool("set_track_folder_depth")
    def set_track_folder_depth(
        ctx: Context, track_index: int, depth: int
    ) -> Dict[str, Any]:
        """
        Set the folder depth of a track.

        Args:
            track_index (int): Index of the track to set folder depth for
            depth (int): Folder depth (0 for normal, 1 for folder, -1 for last in folder)
        """
        return _handle_controller_operation(
            f"Set track {track_index} folder depth to {depth}",
            controller.advanced_routing.set_track_folder_depth,
            track_index,
            depth,
        )

    @mcp.tool("get_track_folder_depth")
    def get_track_folder_depth(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get the folder depth of a track.

        Args:
            track_index (int): Index of the track to get folder depth for
        """
        try:
            depth = controller.advanced_routing.get_track_folder_depth(track_index)
            return _create_success_response(
                f"Track {track_index} folder depth: {depth}"
            )
        except Exception as e:
            logger.error(f"Failed to get track folder depth: {str(e)}")
            return _create_error_response(f"Failed to get track folder depth: {str(e)}")


def _setup_automation_tools(mcp: FastMCP, controller) -> None:
    """Setup automation and modulation MCP tools."""

    @mcp.tool("create_automation_envelope")
    def create_automation_envelope(
        ctx: Context, track_index: int, envelope_name: str
    ) -> Dict[str, Any]:
        """
        Create an automation envelope on a track.

        Args:
            track_index (int): Index of the track to create envelope on
            envelope_name (str): Name of the automation envelope
        """
        return _handle_controller_operation(
            f"Create automation envelope '{envelope_name}' on track {track_index}",
            controller.automation.create_automation_envelope,
            track_index,
            envelope_name,
        )

    @mcp.tool("add_automation_point")
    def add_automation_point(
        ctx: Context,
        track_index: int,
        envelope_name: str,
        time: float,
        value: float,
        shape: int = 0,
    ) -> Dict[str, Any]:
        """
        Add an automation point to an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
            time (float): Time position in seconds (use number, not string)
            value (float): Value of the automation point (use number, not string)
            shape (int): Shape of the automation curve (0: linear, 1: slow, 2: fast, 3: bezier, 4: square)
        """
        return _handle_controller_operation(
            f"Add automation point at {time}s with value {value} on track {track_index}",
            controller.automation.add_automation_point,
            track_index,
            envelope_name,
            time,
            value,
            shape,
        )

    @mcp.tool("get_automation_points")
    def get_automation_points(
        ctx: Context, track_index: int, envelope_name: str
    ) -> Dict[str, Any]:
        """
        Get all automation points from an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
        """
        try:
            points = controller.automation.get_automation_points(
                track_index, envelope_name
            )
            return _create_success_response(
                f"Automation points for '{envelope_name}' on track {track_index}: {points}"
            )
        except Exception as e:
            logger.error(f"Failed to get automation points: {str(e)}")
            return _create_error_response(f"Failed to get automation points: {str(e)}")

    @mcp.tool("set_automation_mode")
    def set_automation_mode(
        ctx: Context, track_index: int, mode: str
    ) -> Dict[str, Any]:
        """
        Set the automation mode for a track.

        Args:
            track_index (int): Index of the track to set automation mode for
            mode (str): Automation mode (e.g., "read", "write", "touch", "latch", "trim")
        """
        return _handle_controller_operation(
            f"Set automation mode to '{mode}' on track {track_index}",
            controller.automation.set_automation_mode,
            track_index,
            mode,
        )

    @mcp.tool("get_automation_mode")
    def get_automation_mode(ctx: Context, track_index: int) -> Dict[str, Any]:
        """
        Get the current automation mode for a track.

        Args:
            track_index (int): Index of the track to get automation mode for
        """
        try:
            mode = controller.automation.get_automation_mode(track_index)
            return _create_success_response(
                f"Track {track_index} automation mode: {mode}"
            )
        except Exception as e:
            logger.error(f"Failed to get automation mode: {str(e)}")
            return _create_error_response(f"Failed to get automation mode: {str(e)}")

    @mcp.tool("delete_automation_point")
    def delete_automation_point(
        ctx: Context, track_index: int, envelope_name: str, point_index: int
    ) -> Dict[str, Any]:
        """
        Delete an automation point from an envelope.

        Args:
            track_index (int): Index of the track containing the envelope
            envelope_name (str): Name of the automation envelope
            point_index (int): Index of the automation point to delete
        """
        return _handle_controller_operation(
            f"Delete automation point {point_index} from '{envelope_name}' on track {track_index}",
            controller.automation.delete_automation_point,
            track_index,
            envelope_name,
            point_index,
        )


def _setup_analysis_tools(mcp: FastMCP, controller) -> None:
    """Setup audio analysis MCP tools for professional mixing and mastering."""

    @mcp.tool("loudness_measure_track")
    def loudness_measure_track(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Measure LUFS loudness metrics for a track.
        
        Args:
            track_index: Index of track to measure
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
        """
        try:
            metrics = controller.analysis.loudness.loudness_measure_track(
                track_index, window_sec, gate_enabled
            )
            if metrics:
                return _create_success_response(
                    f"Track {track_index} loudness: {metrics.integrated_lufs:.1f} LUFS, "
                    f"LRA: {metrics.lra:.1f} LU, True Peak: {metrics.true_peak_dbfs:.1f} dBFS"
                )
            else:
                return _create_error_response("Failed to measure track loudness")
        except Exception as e:
            logger.error(f"Failed to measure track loudness: {e}")
            return _create_error_response(f"Failed to measure track loudness: {str(e)}")

    @mcp.tool("loudness_measure_master")
    def loudness_measure_master(
        ctx: Context, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Measure LUFS loudness metrics for master track.
        
        Args:
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
        """
        try:
            metrics = controller.analysis.loudness.loudness_measure_master(
                window_sec, gate_enabled
            )
            if metrics:
                return _create_success_response(
                    f"Master loudness: {metrics.integrated_lufs:.1f} LUFS, "
                    f"LRA: {metrics.lra:.1f} LU, True Peak: {metrics.true_peak_dbfs:.1f} dBFS"
                )
            else:
                return _create_error_response("Failed to measure master loudness")
        except Exception as e:
            logger.error(f"Failed to measure master loudness: {e}")
            return _create_error_response(f"Failed to measure master loudness: {str(e)}")

    @mcp.tool("spectrum_analyzer_track")
    def spectrum_analyzer_track(
        ctx: Context,
        track_index: int,
        window_size: float = 1.0,
        fft_size: int = 8192,
        weighting: str = "none"
    ) -> Dict[str, Any]:
        """
        Perform FFT spectrum analysis on a track.
        
        Args:
            track_index: Index of track to analyze
            window_size: Analysis window in seconds
            fft_size: FFT size (power of 2)
            weighting: Frequency weighting (A, C, Z, or none)
        """
        try:
            from controllers.analysis.spectrum_controller import WeightingType
            
            weight_map = {
                "none": WeightingType.NONE,
                "A": WeightingType.A_WEIGHTING,
                "C": WeightingType.C_WEIGHTING,
                "Z": WeightingType.Z_WEIGHTING
            }
            weighting_type = weight_map.get(weighting, WeightingType.NONE)
            
            spectrum = controller.analysis.spectrum.spectrum_analyzer_track(
                track_index, window_size, fft_size, weighting_type
            )
            if spectrum:
                return _create_success_response(
                    f"Track {track_index} spectrum analyzed: {len(spectrum.frequencies)} frequency bins, "
                    f"SR: {spectrum.sample_rate}Hz, Weighting: {weighting}"
                )
            else:
                return _create_error_response("Failed to analyze track spectrum")
        except Exception as e:
            logger.error(f"Failed to analyze track spectrum: {e}")
            return _create_error_response(f"Failed to analyze track spectrum: {str(e)}")

    @mcp.tool("phase_correlation")
    def phase_correlation(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Measure phase correlation between L/R channels.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            correlation = controller.analysis.spectrum.phase_correlation(track_index, window_sec)
            if correlation is not None:
                return _create_success_response(
                    f"Track {track_index} phase correlation: {correlation:.3f}"
                )
            else:
                return _create_error_response("Failed to measure phase correlation")
        except Exception as e:
            logger.error(f"Failed to measure phase correlation: {e}")
            return _create_error_response(f"Failed to measure phase correlation: {str(e)}")

    @mcp.tool("stereo_image_metrics")
    def stereo_image_metrics(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Analyze stereo imaging characteristics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            metrics = controller.analysis.spectrum.stereo_image_metrics(track_index, window_sec)
            if metrics:
                return _create_success_response(
                    f"Track {track_index} stereo: Correlation: {metrics.correlation:.3f}, "
                    f"Width: {metrics.width:.2f}, Mid: {metrics.mid_level_db:.1f}dB, "
                    f"Side: {metrics.side_level_db:.1f}dB"
                )
            else:
                return _create_error_response("Failed to analyze stereo image")
        except Exception as e:
            logger.error(f"Failed to analyze stereo image: {e}")
            return _create_error_response(f"Failed to analyze stereo image: {str(e)}")

    @mcp.tool("crest_factor_track")
    def crest_factor_track(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate crest factor (peak-to-RMS ratio) for a track.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            crest = controller.analysis.spectrum.crest_factor_track(track_index, window_sec)
            if crest:
                return _create_success_response(
                    f"Track {track_index} crest factor: {crest.crest_factor_db:.1f}dB "
                    f"(Peak: {crest.peak_db:.1f}dB, RMS: {crest.rms_db:.1f}dB)"
                )
            else:
                return _create_error_response("Failed to calculate crest factor")
        except Exception as e:
            logger.error(f"Failed to calculate crest factor: {e}")
            return _create_error_response(f"Failed to calculate crest factor: {str(e)}")

    @mcp.tool("normalize_track_lufs")
    def normalize_track_lufs(
        ctx: Context,
        track_index: int,
        target_lufs: float = -23.0,
        true_peak_ceiling: float = -1.0
    ) -> Dict[str, Any]:
        """
        Normalize track to target LUFS with true peak ceiling.
        
        Args:
            track_index: Index of track to normalize
            target_lufs: Target LUFS level
            true_peak_ceiling: Maximum true peak in dBFS
        """
        return _handle_controller_operation(
            f"Normalize track {track_index} to {target_lufs} LUFS",
            controller.analysis.loudness.normalize_track_lufs,
            track_index,
            target_lufs,
            true_peak_ceiling
        )

    @mcp.tool("match_loudness_between_tracks")
    def match_loudness_between_tracks(
        ctx: Context,
        source_track: int,
        target_track: int,
        mode: str = "lufs"
    ) -> Dict[str, Any]:
        """
        Match loudness between two tracks.
        
        Args:
            source_track: Track index to adjust
            target_track: Track index to match
            mode: Matching mode (lufs or spectrum)
        """
        return _handle_controller_operation(
            f"Match loudness of track {source_track} to track {target_track}",
            controller.analysis.loudness.match_loudness_between_tracks,
            source_track,
            target_track,
            mode
        )

    @mcp.tool("write_volume_automation_to_target_lufs")
    def write_volume_automation_to_target_lufs(
        ctx: Context,
        track_index: int,
        target_lufs: float = -23.0,
        smoothing_ms: float = 100.0
    ) -> Dict[str, Any]:
        """
        Generate volume automation to achieve target LUFS without clipping.
        
        Args:
            track_index: Index of track to automate
            target_lufs: Target LUFS level
            smoothing_ms: Automation smoothing time in milliseconds
        """
        return _handle_controller_operation(
            f"Write volume automation for track {track_index} to {target_lufs} LUFS",
            controller.analysis.write_volume_automation_to_target_lufs,
            track_index,
            target_lufs,
            smoothing_ms
        )

    @mcp.tool("clip_gain_adjust")
    def clip_gain_adjust(
        ctx: Context,
        track_index: int,
        item_id: int,
        gain_db: float
    ) -> Dict[str, Any]:
        """
        Adjust clip gain on an audio item without affecting track fader.
        
        Args:
            track_index: Index of track containing the item
            item_id: ID of the item to adjust
            gain_db: Gain adjustment in dB
        """
        return _handle_controller_operation(
            f"Adjust clip gain on track {track_index} item {item_id} by {gain_db:+.1f}dB",
            controller.analysis.clip_gain_adjust,
            track_index,
            item_id,
            gain_db
        )

    @mcp.tool("comprehensive_track_analysis")
    def comprehensive_track_analysis(
        ctx: Context,
        track_index: int,
        window_sec: float = 5.0
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including loudness, spectrum, stereo, and dynamics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            analysis = controller.analysis.comprehensive_track_analysis(track_index, window_sec)
            if analysis:
                return _create_success_response(f"Comprehensive analysis for track {track_index}: {analysis}")
            else:
                return _create_error_response("Failed to perform comprehensive analysis")
        except Exception as e:
            logger.error(f"Failed to perform comprehensive analysis: {e}")
            return _create_error_response(f"Failed to perform comprehensive analysis: {str(e)}")

    @mcp.tool("master_chain_analysis")
    def master_chain_analysis(
        ctx: Context,
        window_sec: float = 10.0
    ) -> Dict[str, Any]:
        """
        Analyze master chain for broadcast/streaming compliance and quality.
        
        Args:
            window_sec: Analysis window in seconds
        """
        try:
            analysis = controller.analysis.master_chain_analysis(window_sec)
            if analysis:
                return _create_success_response(f"Master chain analysis: {analysis}")
            else:
                return _create_error_response("Failed to analyze master chain")
        except Exception as e:
            logger.error(f"Failed to analyze master chain: {e}")
            return _create_error_response(f"Failed to analyze master chain: {str(e)}")


def _setup_advanced_item_tools(mcp: FastMCP, controller) -> None:
    """Setup advanced item operations MCP tools."""

    @mcp.tool("split_item")
    def split_item(
        ctx: Context, track_index: int, item_index: int, split_time: float
    ) -> Dict[str, Any]:
        """
        Split an item at a specific time.

        Args:
            track_index (int): Index of the track containing the item
            item_index (int): Index of the item to split
            split_time (float): Time position in seconds to split the item (use number, not string)
        """
        try:
            new_items = controller.advanced_items.split_item(
                track_index, item_index, split_time
            )
            return _create_success_response(
                f"Split item {item_index} at {split_time}s, created {len(new_items)} new items: {new_items}"
            )
        except Exception as e:
            logger.error(f"Failed to split item: {str(e)}")
            return _create_error_response(f"Failed to split item: {str(e)}")

    @mcp.tool("glue_items")
    def glue_items(
        ctx: Context, track_index: int, item_indices: List[int]
    ) -> Dict[str, Any]:
        """
        Glue multiple items together into a single item.

        Args:
            track_index (int): Index of the track containing the items
            item_indices (List[int]): List of indices of items to glue
        """
        return _handle_controller_operation(
            f"Glue {len(item_indices)} items on track {track_index}",
            controller.advanced_items.glue_items,
            track_index,
            item_indices,
        )

    @mcp.tool("fade_in")
    def fade_in(
        ctx: Context,
        track_index: int,
        item_index: int,
        fade_length: float,
        fade_curve: int = 0,
    ) -> Dict[str, Any]:
        """
        Add a fade-in to an item.

        Args:
            track_index (int): Index of the track containing the item
            item_index (int): Index of the item to add fade-in to
            fade_length (float): Length of the fade-in in seconds (use number, not string)
            fade_curve (int): Fade curve shape (0-6, default 0: linear)
        """
        return _handle_controller_operation(
            f"Add {fade_length}s fade-in to item {item_index} on track {track_index}",
            controller.advanced_items.fade_in,
            track_index,
            item_index,
            fade_length,
            fade_curve,
        )

    @mcp.tool("fade_out")
    def fade_out(
        ctx: Context,
        track_index: int,
        item_index: int,
        fade_length: float,
        fade_curve: int = 0,
    ) -> Dict[str, Any]:
        """
        Add a fade-out to an item.

        Args:
            track_index (int): Index of the track containing the item
            item_index (int): Index of the item to add fade-out to
            fade_length (float): Length of the fade-out in seconds (use number, not string)
            fade_curve (int): Fade curve shape (0-6, default 0: linear)
        """
        return _handle_controller_operation(
            f"Add {fade_length}s fade-out to item {item_index} on track {track_index}",
            controller.advanced_items.fade_out,
            track_index,
            item_index,
            fade_length,
            fade_curve,
        )

    @mcp.tool("crossfade_items")
    def crossfade_items(
        ctx: Context,
        track_index: int,
        item1_index: int,
        item2_index: int,
        crossfade_length: float,
    ) -> Dict[str, Any]:
        """
        Create a crossfade between two items.

        Args:
            track_index (int): Index of the track containing the items
            item1_index (int): Index of the first item
            item2_index (int): Index of the second item
            crossfade_length (float): Length of the crossfade in seconds (use number, not string)
        """
        return _handle_controller_operation(
            f"Create {crossfade_length}s crossfade between items {item1_index} and {item2_index}",
            controller.advanced_items.crossfade_items,
            track_index,
            item1_index,
            item2_index,
            crossfade_length,
        )

    @mcp.tool("reverse_item")
    def reverse_item(ctx: Context, track_index: int, item_index: int) -> Dict[str, Any]:
        """
        Reverse an item.

        Args:
            track_index (int): Index of the track containing the item
            item_index (int): Index of the item to reverse
        """
        return _handle_controller_operation(
            f"Reverse item {item_index} on track {track_index}",
            controller.advanced_items.reverse_item,
            track_index,
            item_index,
        )

    @mcp.tool("get_item_fade_info")
    def get_item_fade_info(
        ctx: Context, track_index: int, item_index: int
    ) -> Dict[str, Any]:
        """
        Get fade information for an item.

        Args:
            track_index (int): Index of the track containing the item
            item_index (int): Index of the item to get fade info for
        """
        try:
            fade_info = controller.advanced_items.get_item_fade_info(
                track_index, item_index
            )
            return _create_success_response(
                f"Fade info for item {item_index} on track {track_index}: {fade_info}"
            )
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
    _setup_analysis_tools(mcp, controller)
