import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


def get_reapy():
    """Lazy import of reapy."""
    try:
        import reapy
        return reapy
    except ImportError as e:
        logging.error(f"Failed to import reapy: {e}")
        raise


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
        logging.error(f"Failed to get item: {e}")
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
        logging.error(f"Failed to get item properties: {e}")
        return None


def get_source_filename(take: Any) -> str:
    """Get the source filename from a take."""
    try:
        if (hasattr(take, 'source') and 
            hasattr(take.source, 'filename')):
            return take.source.filename
        return ""
    except Exception as e:
        logging.error(f"Failed to get source filename: {e}")
        return "" 
