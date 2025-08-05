import logging
from typing import Optional, List, Dict, Any, Union


def get_reapy():
    """Lazy import of reapy."""
    try:
        import reapy
        return reapy
    except ImportError as e:
        logging.error(f"Failed to import reapy: {e}")
        raise


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
            logging.error(f"Item {item_id} not found on track {track_index}")
            return None
        
        # Duplicate the item
        new_item = original_item.copy()
        
        # Set new position if provided
        if new_position is not None:
            new_item.position = new_position
        
        return new_item.id
        
    except Exception as e:
        logging.error(f"Failed to duplicate item {item_id}: {e}")
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
        reapy = get_reapy()
        project = reapy.Project()
        track = project.tracks[track_index]
        
        # Find and delete the item
        for item in track.items:
            if item.id == item_id:
                item.delete()
                return True
        
        logging.error(f"Item {item_id} not found on track {track_index}")
        return False
        
    except Exception as e:
        logging.error(f"Failed to delete item {item_id}: {e}")
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
        logging.debug(f"Error during deletion verification (likely item was deleted): {e}")
        return True


def get_items_in_time_range(track_index: int, start_time: float, end_time: float) -> List[Dict[str, Any]]:
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
            
            if (item_start < end_time and item_end > start_time):
                items_in_range.append({
                    'id': item.id,
                    'position': item.position,
                    'length': item.length,
                    'start': item.start,
                    'end': item.end,
                    'selected': item.selected,
                    'muted': item.muted
                })
        
        return items_in_range
        
    except Exception as e:
        logging.error(f"Failed to get items in time range: {e}")
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
                    selected_items.append({
                        'track_index': track.index,
                        'id': item.id,
                        'position': item.position,
                        'length': item.length,
                        'start': item.start,
                        'end': item.end,
                        'muted': item.muted
                    })
        
        return selected_items
        
    except Exception as e:
        logging.error(f"Failed to get selected items: {e}")
        return [] 
