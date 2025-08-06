"""
Item duplication operations for REAPER items.
Focused module for creating copies of existing items.
"""
import logging
from typing import Optional

from ..core.reapy_bridge import get_reapy

logger = logging.getLogger(__name__)


def duplicate_item(track_index: int, item_id: int, new_position: Optional[float] = None) -> Optional[int]:
    """
    Duplicate an item on a track.
    
    Args:
        track_index (int): Index of the track
        item_id (int): ID of the item to duplicate
        new_position (Optional[float]): New position for the duplicated item
        
    Returns:
        Optional[int]: ID of the new item if successful, None otherwise
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]
        
        # Find the original item
        original_item = None
        for item in track.items:
            if item.id == item_id:
                original_item = item
                break
        
        if original_item is None:
            logger.error(f"Item {item_id} not found on track {track_index}")
            return None
        
        # Duplicate the item
        new_item = original_item.copy()
        
        # Set new position if provided
        if new_position is not None:
            new_item.position = new_position
        
        return new_item.id
        
    except Exception as e:
        logger.error(f"Failed to duplicate item {item_id}: {e}")
        return None