"""
Item lifecycle operations for REAPER items.
Backward compatibility wrapper that re-exports from specialized modules.
"""

# Import from specialized modules
from .duplication import duplicate_item
from .deletion import delete_item, verify_item_deletion

# Re-export all functions for backward compatibility
__all__ = [
    'duplicate_item',
    'delete_item', 
    'verify_item_deletion'
]