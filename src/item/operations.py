"""
Item operations module for REAPER items.
Backward compatibility wrapper that re-exports from specialized modules.
"""

# Import from specialized modules
from .duplication import duplicate_item
from .deletion import delete_item, verify_item_deletion
from .queries import get_items_in_time_range, get_selected_items

# Re-export all functions for backward compatibility
__all__ = [
    'duplicate_item', 
    'delete_item', 
    'verify_item_deletion',
    'get_items_in_time_range', 
    'get_selected_items'
]