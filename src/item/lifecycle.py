"""
Item lifecycle operations for REAPER items.
Backward compatibility wrapper that re-exports from the core module.
"""

# Import from core module
from .core import (
    duplicate_item,
    delete_item, 
    verify_item_deletion
)

# Re-export all functions for backward compatibility
__all__ = [
    'duplicate_item',
    'delete_item', 
    'verify_item_deletion'
]