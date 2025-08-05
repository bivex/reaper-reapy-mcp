"""
Utility module for reapy initialization to avoid circular imports.
"""
import logging

_reapy_instance = None
_rpr_instance = None

def get_reapy():
    """Get reapy instance with lazy initialization."""
    global _reapy_instance, _rpr_instance
    
    if _reapy_instance is None:
        try:
            import importlib
            reapy_module = importlib.import_module('reapy')
            _reapy_instance = reapy_module
            _rpr_instance = reapy_module.reascript_api
        except ImportError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to import reapy: {e}")
            raise
    
    return _reapy_instance

def get_rpr():
    """Get reapy.reascript_api instance."""
    get_reapy()  # Ensure reapy is initialized
    return _rpr_instance