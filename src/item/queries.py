"""
Item query operations for REAPER items.
Provides functionality for finding and retrieving item information.
"""
import logging
from typing import List, Dict, Any

from ..core.reapy_bridge import get_reapy

logger = logging.getLogger(__name__)


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