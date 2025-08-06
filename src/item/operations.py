"""
Item operations module for REAPER items.
Backward compatibility wrapper that re-exports from consolidated modules.
"""

# Import from consolidated modules
from .management import duplicate_item, delete_item, verify_item_deletion
from .access import get_items_in_time_range, get_selected_items

# Re-export all functions for backward compatibility
__all__ = [
    'duplicate_item', 
    'delete_item', 
    'verify_item_deletion',
    'get_items_in_time_range', 
    'get_selected_items'
]