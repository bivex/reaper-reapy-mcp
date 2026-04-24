"""FX-related MCP tools."""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from .tool_helpers import (
    _create_success_response,
    _create_error_response,
    _handle_controller_operation,
)

logger = logging.getLogger(__name__)


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
                    f"Added FX {fx_name} to track {track_index} at index {fx_index}"
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
                else "disabled"
                if enable is False
                else "toggled"
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
