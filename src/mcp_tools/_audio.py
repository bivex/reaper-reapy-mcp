"""MCP tools for audio items and properties."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Any, Dict, List, Optional, Set
try:
    from src.time.conversion import parse_position
except ImportError:
    from time.conversion import parse_position
from ._helpers import (
    _create_success_response,
    _create_error_response,
    _handle_controller_operation,
    logger,
)


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
