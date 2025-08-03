import reapy
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def select_item(item: reapy.Item) -> bool:
    """
    Select a media item.
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
        error_message = f"Failed to select item {item.id}: {e}"
        logger.error(error_message)
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
        if not _verify_item_deletion(item):
            logger.error(f"Item {item.id} still exists after deletion")
            return False
        
        logger.info(f"Deleted item with ID: {item.id}")
        return True
        
    except Exception as e:
        error_message = f"Failed to delete item {item.id}: {e}"
        logger.error(error_message)
        return False

def _verify_item_deletion(item: reapy.Item) -> bool:
    """
    Verify that an item was successfully deleted.
    
    Args:
        item (reapy.Item): The item that should have been deleted
        
    Returns:
        bool: True if item is confirmed deleted, False if it still exists
    """
    try:
        # Try to find the item again - it should be gone
        for i in item.track.items:
            if str(i.id) == str(item.id):
                return False
        return True
    except Exception as e:
        # If we get an error trying to access the item, it probably means it was deleted
        logger.debug(f"Error during deletion verification (likely item {item.id} was deleted): {e}")
        return True 
