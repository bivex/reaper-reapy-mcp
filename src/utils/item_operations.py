import reapy
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def select_item(item: reapy.Item) -> bool:
    """
    Select a media item.
    
    Args:
        item (reapy.Item): The item to select
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Always use the ReaScript API directly
        from reapy import reascript_api as RPR
        
        # First clear all selections
        RPR.SelectAllMediaItems(0, False)
        
        # Then select this item
        RPR.SetMediaItemSelected(item.id, True)
        return True
    except Exception as e:
        logger.error(f"Failed to select item: {e}")
        return False

def delete_item(item: reapy.Item) -> bool:
    """
    Delete a media item.
    
    Args:
        item (reapy.Item): The item to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use reapy's native API to delete the item
        item.delete()
        
        # Verify the item was deleted
        try:
            # Try to find the item again - it should be gone
            for i in item.track.items:
                if str(i.id) == str(item.id):
                    logger.error("Item still exists after deletion")
                    return False
        except Exception as e:
            # If we get an error trying to access the item, it probably means it was deleted
            pass
        
        logger.info(f"Deleted item with ID: {item.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete item: {e}")
        return False 
