"""
Item access operations for REAPER items.
Provides functionality for querying items and accessing their properties.
"""
import logging
from typing import Optional, Dict, Any, Union, List

from ..core.reapy_bridge import get_reapy

logger = logging.getLogger(__name__)


def get_item_by_id_or_index(track_index: int, item_id_or_index: Union[int, str]) -> Optional[Any]:
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


def get_item_properties(track_index: int, item_id_or_index: Union[int, str]) -> Optional[Dict[str, Any]]:
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
            'id': item.id,
            'position': item.position,
            'length': item.length,
            'start': item.start,
            'end': item.end,
            'selected': item.selected,
            'muted': item.muted,
            'locked': item.locked,
            'snap_offset': item.snap_offset,
            'take_count': len(item.takes)
        }
        
    except Exception as e:
        logger.error(f"Failed to get item properties: {e}")
        return None


def get_source_filename(take: Any) -> str:
    """Get the source filename from a take."""
    try:
        if (hasattr(take, 'source') and 
            hasattr(take.source, 'filename')):
            return take.source.filename
        return ""
    except Exception as e:
        logger.error(f"Failed to get source filename: {e}")
        return ""


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
        logger.error(f"Failed to get selected items: {e}")
        return []