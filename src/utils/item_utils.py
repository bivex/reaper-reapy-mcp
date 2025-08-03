import reapy
import logging
from typing import Union, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_item_by_id_or_index(track: reapy.Track, 
                           item_id: Union[int, str]) -> Optional[reapy.Item]:
    """
    Get an item from a track by its ID or index. Returns the found item or None.
    
    Args:
        track (reapy.Track): The track to search in
        item_id (Union[int, str]): The item ID or index
        
    Returns:
        Optional[reapy.Item]: The found item or None if not found
    """
    try:
        # Try to use item_id as an index
        item_index = int(item_id)
        if 0 <= item_index < len(track.items):
            item = track.items[item_index]
            logger.debug(f"Found item at index: {item_index}")
            return item
    except ValueError:
        # If conversion fails, try to match by string ID
        str_item_id = str(item_id)
        for i in track.items:
            if str(i.id) == str_item_id:
                logger.debug(f"Found item with ID: {item_id}")
                return i
    
    logger.error(f"Item with ID {item_id} not found")
    return None

def get_item_properties(item: reapy.Item) -> Dict[str, Any]:
    """
    Get properties of a media item.
    
    Args:
        item (reapy.Item): The item to get properties from
        
    Returns:
        Dict[str, Any]: Dictionary of item properties
    """
    try:
        # Get basic properties
        position = item.position
        length = item.length
        name = item.active_take.name if item.active_take else ""
        
        # Determine if it's an audio item
        is_audio = False
        source_file = ""
        take = item.active_take
        if take and not take.is_midi:
            is_audio = True
            try:
                source_file = _get_source_filename(take)
            except Exception as e:
                logger.warning(f"Failed to get source filename: {e}")
        
        # Get muted and selected state
        is_muted = item.muted if hasattr(item, 'muted') else False
        is_selected = item.selected if hasattr(item, 'selected') else False
        
        return {
            'position': position,
            'length': length,
            'name': name,
            'is_audio': is_audio,
            'file_path': source_file,
            'muted': is_muted,
            'selected': is_selected
        }
    except Exception as e:
        error_message = f"Failed to get item properties for item {item.id}: {e}"
        logger.error(error_message)
        return {}

def _get_source_filename(take: reapy.Take) -> str:
    """Get the source filename from a take."""
    if (hasattr(take, 'source') and 
        hasattr(take.source, 'filename')):
        return take.source.filename
    return "" 
