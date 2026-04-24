"""MCP tools for routing, sends, buses, sidechain."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

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


def _setup_sidechain_tools(mcp: FastMCP, controller) -> None:
    """Setup sidechain and bus routing MCP tools."""

    @mcp.tool("create_sidechain_send")
    def create_sidechain_send(
        ctx: Context,
        source_track: int,
        destination_track: int,
        dest_channels: int = 3,
        level_db: float = 0.0,
        pre_fader: bool = True
    ) -> Dict[str, Any]:
        """
        Create a sidechain send between tracks for ducking/compression.
        
        Args:
            source_track (int): Index of the source track (e.g., kick drum)
            destination_track (int): Index of the destination track (e.g., bass with compressor)
            dest_channels (int): Destination channels (3 for channels 3/4, 1 for channels 1/2)
            level_db (float): Send level in dB
            pre_fader (bool): True for pre-fader, False for post-fader
        """
        try:
            result = controller.sidechain.create_sidechain_send(
                source_track=source_track,
                destination_track=destination_track,
                dest_channels=dest_channels,
                level_db=level_db,
                pre_fader=pre_fader
            )
            if result:
                return {
                    "status": "success",
                    "message": f"Created sidechain send: track {source_track} -> track {destination_track}",
                    "data": {
                        "send_id": result.send_id,
                        "sidechain_channels": result.sidechain_channels,
                        "level_db": result.level_db,
                        "pre_fader": result.pre_fader,
                        "latency_ms": result.latency_ms,
                        "route_valid": result.route_valid
                    }
                }
            else:
                return _create_error_response("Failed to create sidechain send")
        except Exception as e:
            logger.error(f"Failed to create sidechain send: {str(e)}")
            return _create_error_response(f"Failed to create sidechain send: {str(e)}")

    @mcp.tool("setup_parallel_bus")
    def setup_parallel_bus(
        ctx: Context,
        source_track: int,
        bus_name: str,
        mix_db: float = -6.0,
        latency_comp: bool = True
    ) -> Dict[str, Any]:
        """
        Create a parallel processing bus with phase compensation.
        
        Args:
            source_track (int): Index of the source track
            bus_name (str): Name for the parallel bus track
            mix_db (float): Mix level for parallel processing in dB
            latency_comp (bool): Enable automatic latency compensation
        """
        try:
            result = controller.sidechain.setup_parallel_bus(
                source_track=source_track,
                bus_name=bus_name,
                mix_db=mix_db,
                latency_comp=latency_comp
            )
            if result:
                return {
                    "status": "success",
                    "message": f"Created parallel bus '{bus_name}' for track {source_track}",
                    "data": {
                        "bus_track_index": result.bus_track_index,
                        "send_id": result.send_id,
                        "return_send_id": result.return_send_id,
                        "mix_db": result.mix_db,
                        "latency_compensation": result.latency_compensation
                    }
                }
            else:
                return _create_error_response("Failed to setup parallel bus")
        except Exception as e:
            logger.error(f"Failed to setup parallel bus: {str(e)}")
            return _create_error_response(f"Failed to setup parallel bus: {str(e)}")

    @mcp.tool("add_saturation_bus")
    def add_saturation_bus(
        ctx: Context,
        source_track: int,
        saturation_type: str,
        mix_percent: float = 30.0
    ) -> Dict[str, Any]:
        """
        Create a saturation bus for parallel harmonic enhancement.
        
        Args:
            source_track (int): Index of the source track
            saturation_type (str): Type of saturation ("tape", "tube", "transistor", "digital")
            mix_percent (float): Saturation mix percentage (0-100%)
        """
        try:
            result = controller.sidechain.add_saturation_bus(
                source_track=source_track,
                saturation_type=saturation_type,
                mix_percent=mix_percent
            )
            if result:
                return {
                    "status": "success",
                    "message": f"Created {saturation_type} saturation bus for track {source_track}",
                    "data": {
                        "bus_track_index": result.bus_track_index,
                        "saturation_fx_id": result.saturation_fx_id,
                        "saturation_type": result.saturation_type,
                        "send_id": result.send_id,
                        "return_send_id": result.return_send_id,
                        "mix_percent": result.mix_percent
                    }
                }
            else:
                return _create_error_response("Failed to create saturation bus")
        except Exception as e:
            logger.error(f"Failed to create saturation bus: {str(e)}")
            return _create_error_response(f"Failed to create saturation bus: {str(e)}")

    @mcp.tool("sidechain_route_analyzer")
    def sidechain_route_analyzer(
        ctx: Context,
        source_track: int,
        dest_track: int
    ) -> Dict[str, Any]:
        """
        Analyze sidechain routing validity and configuration.
        
        Args:
            source_track (int): Index of the source track
            dest_track (int): Index of the destination track
        """
        try:
            result = controller.sidechain.sidechain_route_analyzer(
                source_track=source_track,
                dest_track=dest_track
            )
            return {
                "status": "success" if result.valid else "warning",
                "message": f"Route analysis: {source_track} -> {dest_track}",
                "data": {
                    "valid": result.valid,
                    "channels_map": result.channels_map,
                    "latency_ms": result.latency_ms,
                    "warnings": result.warnings,
                    "errors": result.errors
                }
            }
        except Exception as e:
            logger.error(f"Failed to analyze sidechain route: {str(e)}")
            return _create_error_response(f"Failed to analyze sidechain route: {str(e)}")


