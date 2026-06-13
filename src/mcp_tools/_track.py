"""MCP tools for track management."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Any, Dict, Optional, Set
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

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


