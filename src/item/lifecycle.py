"""
Item lifecycle operations for REAPER items.
Backward compatibility wrapper that re-exports from consolidated modules.
"""

# Import from consolidated modules
from .management import duplicate_item, delete_item, verify_item_deletion

# Re-export all functions for backward compatibility
__all__ = [
    'duplicate_item',
    'delete_item', 
    'verify_item_deletion'
]