"""
Item deletion operations for REAPER items.
Focused module for removing items and verifying deletion.
"""
import logging
from typing import Any

from ..core.reapy_bridge import get_reapy

logger = logging.getLogger(__name__)


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
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]
        
        # Find and delete the item
        for item in track.items:
            if item.id == item_id:
                item.delete()
                return True
        
        logger.error(f"Item {item_id} not found on track {track_index}")
        return False
        
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
        logger.debug(f"Error during deletion verification (likely item was deleted): {e}")
        return True