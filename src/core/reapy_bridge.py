"""
Centralized REAPER API bridge for consistent reapy access across the application.
This module provides a single point of access to reapy instances to avoid
circular imports and duplicate initialization code.
"""
import logging
import importlib

logger = logging.getLogger(__name__)

_reapy_instance = None
_rpr_instance = None


def get_reapy():
    """
    Get reapy instance with lazy initialization.
    
    Returns:
        reapy module: The reapy module instance
        
    Raises:
        ImportError: If reapy cannot be imported
    """
    global _reapy_instance, _rpr_instance
    
    if _reapy_instance is None:
        try:
            reapy_module = importlib.import_module('reapy')
            _reapy_instance = reapy_module
            _rpr_instance = reapy_module.reascript_api
            logger.debug("Reapy module initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import reapy: {e}")
            raise
    
    return _reapy_instance


def get_rpr():
    """
    Get reapy.reascript_api instance.
    
    Returns:
        ReaScript API instance for low-level REAPER operations
    """
    get_reapy()  # Ensure reapy is initialized
    return _rpr_instance


def reset_instances():
    """
    Reset the cached instances. Useful for testing.
    """
    global _reapy_instance, _rpr_instance
    _reapy_instance = None
    _rpr_instance = None