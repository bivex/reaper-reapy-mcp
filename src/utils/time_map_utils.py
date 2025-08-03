import reapy
from reapy import reascript_api as RPR
from typing import Dict
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Constants to replace magic numbers
DEFAULT_BPM = 120.0
DEFAULT_TIME_SIG_NUM = 4
DEFAULT_TIME_SIG_DEN = 4

def get_time_map_info(project=None) -> dict:
    """
    Get time map information for the project.
    
    Args:
        project: Optional reapy.Project instance. If None, current project is used.
        
    Returns:
        dict: Time map information including:
            - bpm: Current tempo in BPM
            - time_sig_num: Time signature numerator
            - time_sig_den: Time signature denominator
    """
    if project is None:
        project = reapy.Project()
        
    try:
        # Get time signature at current cursor
        time_sig_num, time_sig_den = RPR.TimeMap_GetTimeSigAtTime(project.id, 0)
        
        return {
            'bpm': project.bpm,
            'time_sig_num': time_sig_num,
            'time_sig_den': time_sig_den
        }
    except Exception as e:
        # Log the error and return defaults if getting info fails
        logger.warning(f"Failed to get time map info from project: {e}. Using default values.")
        return _get_default_time_map_info()

def _get_default_time_map_info() -> Dict:
    """Get default time map information."""
    return {
        'bpm': DEFAULT_BPM,
        'time_sig_num': DEFAULT_TIME_SIG_NUM,
        'time_sig_den': DEFAULT_TIME_SIG_DEN
    } 
