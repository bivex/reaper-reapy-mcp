"""
Item utility functions for REAPER items.
Backward compatibility wrapper that re-exports from consolidated modules.
"""

# Import from consolidated modules
from .access import get_item_by_id_or_index, get_item_properties, get_source_filename

# Re-export all functions for backward compatibility
__all__ = [
    'get_item_by_id_or_index',
    'get_item_properties', 
    'get_source_filename'
]