import reapy
from reapy import reascript_api as RPR
from typing import Dict

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
        # Return defaults if getting info fails
        return {
            'bpm': 120.0,
            'time_sig_num': 4,
            'time_sig_den': 4
        } 
