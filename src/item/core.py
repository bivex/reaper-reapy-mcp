"""
Core REAPER item operations.
Comprehensive module providing all item-related functionality in a cohesive structure.

This module organizes item operations into logical groups with high cohesion:
- Item property access and utilities
- Item querying and selection
- Item lifecycle management (create, duplicate, delete)
"""

import logging
from typing import Optional, Dict, Any, Union, List

from ..core.reapy_bridge import get_reapy

logger = logging.getLogger(__name__)


# =============================================================================
# ITEM PROPERTY ACCESS AND UTILITIES
# =============================================================================


def get_item_by_id_or_index(
    track_index: int, item_id_or_index: Union[int, str]
) -> Optional[Any]:
    """
    Get an item by its ID or index.

    Args:
        track_index (int): Index of the track
        item_id_or_index (Union[int, str]): Item ID or index

    Returns:
        Optional[Any]: Item object if found, None otherwise
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]

        if isinstance(item_id_or_index, int):
            # Treat as index
            if 0 <= item_id_or_index < len(track.items):
                return track.items[item_id_or_index]
        else:
            # Treat as ID
            for item in track.items:
                if str(item.id) == str(item_id_or_index):
                    return item

        return None

    except Exception as e:
        logger.error(f"Failed to get item: {e}")
        return None


def get_item_properties(
    track_index: int, item_id_or_index: Union[int, str]
) -> Optional[Dict[str, Any]]:
    """
    Get properties of an item.

    Args:
        track_index (int): Index of the track
        item_id_or_index (Union[int, str]): Item ID or index

    Returns:
        Optional[Dict[str, Any]]: Item properties if found, None otherwise
    """
    try:
        item = get_item_by_id_or_index(track_index, item_id_or_index)
        if item is None:
            return None

        return {
            "id": item.id,
            "position": item.position,
            "length": item.length,
            "start": item.start,
            "end": item.end,
            "selected": item.selected,
            "muted": item.muted,
            "locked": item.locked,
            "snap_offset": item.snap_offset,
            "take_count": len(item.takes),
        }

    except Exception as e:
        logger.error(f"Failed to get item properties: {e}")
        return None


def get_source_filename(take: Any) -> str:
    """
    Get the source filename from a take.

    Args:
        take: The take object to get filename from

    Returns:
        str: Source filename or empty string if not available
    """
    try:
        if hasattr(take, "source") and hasattr(take.source, "filename"):
            return take.source.filename
        return ""
    except Exception as e:
        logger.error(f"Failed to get source filename: {e}")
        return ""


# =============================================================================
# ITEM QUERYING AND SELECTION
# =============================================================================


def get_items_in_time_range(
    track_index: int, start_time: float, end_time: float
) -> List[Dict[str, Any]]:
    """
    Get all items in a time range on a track.

    Args:
        track_index (int): Index of the track
        start_time (float): Start time in seconds
        end_time (float): End time in seconds

    Returns:
        List[Dict[str, Any]]: List of item information
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]

        items_in_range = []
        for item in track.items:
            # Check if item overlaps with the time range
            item_start = item.position
            item_end = item.position + item.length

            if item_start < end_time and item_end > start_time:
                items_in_range.append(
                    {
                        "id": item.id,
                        "position": item.position,
                        "length": item.length,
                        "start": item.start,
                        "end": item.end,
                        "selected": item.selected,
                        "muted": item.muted,
                    }
                )

        return items_in_range

    except Exception as e:
        logger.error(f"Failed to get items in time range: {e}")
        return []


def get_selected_items() -> List[Dict[str, Any]]:
    """
    Get all selected items across all tracks.

    Returns:
        List[Dict[str, Any]]: List of selected item information
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()

        selected_items = []
        for track in project.tracks:
            for item in track.items:
                if item.selected:
                    selected_items.append(
                        {
                            "track_index": track.index,
                            "id": item.id,
                            "position": item.position,
                            "length": item.length,
                            "start": item.start,
                            "end": item.end,
                            "muted": item.muted,
                        }
                    )

        return selected_items

    except Exception as e:
        logger.error(f"Failed to get selected items: {e}")
        return []


def select_item(item: Any) -> bool:
    """
    Select a specific item.

    Args:
        item: The item to select

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Clear all selections first
        reapy = get_reapy()
        project = reapy.Project()

        # Deselect all items
        for track in project.tracks:
            for track_item in track.items:
                track_item.selected = False

        # Select the target item
        item.selected = True

        logger.info(f"Selected item {item.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to select item: {e}")
        return False


# =============================================================================
# ITEM LIFECYCLE MANAGEMENT
# =============================================================================


def duplicate_item(
    track_index: int, item_id: int, new_position: Optional[float] = None
) -> Optional[int]:
    """
    Duplicate an item on a track and return the concrete index of the new item.

    Behavior:
    - Accepts item_id as either a track index or a concrete identifier that
      get_item_by_id_or_index can resolve.
    - Duplicates the item using the underlying API.
    - If new_position is provided, repositions the duplicated item.
    - Returns the new item's index within track.items (stable int), not a
      handle or sentinel.

    Args:
        track_index (int): Index of the track
        item_id (int): ID or index of the item to duplicate
        new_position (Optional[float]): New position for the duplicated item

    Returns:
        Optional[int]: Concrete index of the new item within the track if
        successful, None otherwise
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]

        # Resolve original item from id or index
        original_item = get_item_by_id_or_index(track_index, item_id)
        if original_item is None:
            logger.error(f"Item {item_id} not found on track {track_index}")
            return None

        # Capture a snapshot of existing item ids to detect the new one
        before_ids = set()
        for it in track.items:
            try:
                before_ids.add(it.id)
            except Exception:
                # Ignore items that fail to expose id during snapshot
                pass

        # Duplicate the item. Prefer API duplication if available,
        # otherwise fallback to copy()
        new_item = None
        try:
            if hasattr(original_item, "duplicate"):
                new_item = original_item.duplicate()
            else:
                new_item = original_item.copy()
        except Exception as e_dup:
            logger.error(
                f"Underlying duplication failed for item {item_id} on track {track_index}: {e_dup}"
            )
            return None

        # Optionally reposition the new item
        if new_item is not None and new_position is not None:
            try:
                new_item.position = new_position
            except Exception as e_pos:
                logger.warning(
                    f"Failed to set position {new_position} for duplicated item on track {track_index}: {e_pos}"
                )

        # Commit/refresh project state if necessary (some hosts require updates)
        try:
            if hasattr(project, "update_timeline"):
                project.update_timeline()
        except Exception:
            pass

        # Identify the newly created item by comparing ids after duplication
        new_index = None
        try:
            for idx, it in enumerate(track.items):
                try:
                    if it.id not in before_ids:
                        new_index = idx
                        break
                except Exception:
                    # Skip items that don't expose id
                    continue
        except Exception as e_scan:
            logger.warning(
                f"Failed scanning for new item index on track {track_index}: {e_scan}"
            )

        # Fallback: if IDs are not comparable, try heuristics via nearest position
        if new_index is None and new_item is not None:
            try:
                target_pos = getattr(new_item, "position", None)
                if target_pos is not None:
                    best_idx = None
                    best_diff = None
                    for idx, it in enumerate(track.items):
                        try:
                            diff = abs((it.position or 0.0) - target_pos)
                        except Exception:
                            continue
                        if best_diff is None or diff < best_diff:
                            best_diff = diff
                            best_idx = idx
                    new_index = best_idx
            except Exception as e_heur:
                logger.debug(f"Heuristic index resolution failed: {e_heur}")

        # Final guard: ensure we return a proper integer index
        if isinstance(new_index, int) and 0 <= new_index < len(track.items):
            logger.info(
                "Duplicated item %s on track %s -> new index %s",
                item_id,
                track_index,
                new_index,
            )
            return new_index

        # As a last resort, try to return index of 'new_item' if it exists
        # within track.items by identity
        if new_item is not None:
            try:
                for idx, it in enumerate(track.items):
                    if it is new_item:
                        return idx
            except Exception:
                pass

        logger.error(
            "Could not resolve new item index after duplication of %s on track %s",
            item_id,
            track_index,
        )
        return None

    except Exception as e:
        logger.error("Failed to duplicate item %s: %s", item_id, e)
        return None


def delete_item(track_index: int, item_id: int) -> bool:
    """
    Delete an item from a track.

    Args:
        track_index (int): Index of the track
        item_id (int): ID of the item to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find the item using our utility function
        item = get_item_by_id_or_index(track_index, item_id)
        if item is None:
            logger.error(f"Item {item_id} not found on track {track_index}")
            return False

        # Delete the item
        item.delete()
        return True

    except Exception as e:
        logger.error(f"Failed to delete item {item_id}: {e}")
        return False


def verify_item_deletion(item: Any) -> bool:
    """
    Verify that an item was successfully deleted.

    Args:
        item: The item to verify deletion for

    Returns:
        bool: True if item was deleted, False otherwise
    """
    try:
        # Try to access the item - if it's deleted, this should fail
        _ = item.id
        return False
    except Exception as e:
        # If we get an error trying to access the item, it probably means it was deleted
        logger.debug(
            f"Error during deletion verification (likely item was deleted): {e}"
        )
        return True
