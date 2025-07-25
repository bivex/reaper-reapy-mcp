import reapy
from reapy import reascript_api as RPR
from typing import Union, Tuple

def position_to_time(position: Union[float, str], project=None) -> float:
    """
    Convert a position (time in seconds or measure:beat string) to time in seconds.
    
    Args:
        position: Either a float (time in seconds) or string in format "measure:beat"
        project: Optional reapy.Project instance. If None, current project is used.
        
    Returns:
        float: Time position in seconds
    """
    if isinstance(position, (int, float)):
        return float(position)
        
    if isinstance(position, str) and ':' in position:
        measure, beat = map(float, position.split(':'))
        if project is None:
            project = reapy.Project()
        
        try:
            # Use the project's tempo and time signature for conversion
            bpm = project.bpm
            beats_per_measure = 4  # Default to 4/4 time signature
            
            # Try to get actual time signature if possible
            try:
                time_sig_num, time_sig_den = RPR.TimeMap_GetTimeSigAtTime(project.id, 0)
                if time_sig_num > 0:
                    beats_per_measure = time_sig_num
            except:
                pass  # Use default if getting time signature fails
            
            seconds_per_beat = 60.0 / bpm
            seconds_per_measure = seconds_per_beat * beats_per_measure
            
            # Convert measure:beat to time
            # Measures are 1-based in our interface
            time = (measure - 1) * seconds_per_measure + (beat - 1) * seconds_per_beat
            return time
        except Exception as e:
            # Ultimate fallback - just return the beat value as seconds
            return beat
        
    return float(position)  # Try direct conversion

def time_to_measure(time: float, project=None) -> str:
    """
    Convert time in seconds to measure:beat string.
    
    Args:
        time: Time position in seconds
        project: Optional reapy.Project instance. If None, current project is used.
        
    Returns:
        str: Position as "measure:beat" string
    """
    if project is None:
        project = reapy.Project()
    
    try:
        # Use the project's tempo and time signature for conversion
        bpm = project.bpm
        beats_per_measure = 4  # Default to 4/4 time signature
        
        # Try to get actual time signature if possible
        try:
            time_sig_num, time_sig_den = RPR.TimeMap_GetTimeSigAtTime(project.id, 0)
            if time_sig_num > 0:
                beats_per_measure = time_sig_num
        except:
            pass  # Use default if getting time signature fails
        
        seconds_per_beat = 60.0 / bpm
        seconds_per_measure = seconds_per_beat * beats_per_measure
        
        # Convert time to measure:beat
        measure = int(time // seconds_per_measure) + 1  # 1-based measure
        beat_time = time % seconds_per_measure
        beat = (beat_time / seconds_per_beat) + 1  # 1-based beat
        
        return f"{measure}:{beat:.3f}"
    except Exception as e:
        # Fallback: estimate based on 120 BPM, 4/4 time
        seconds_per_beat = 0.5  # 120 BPM
        seconds_per_measure = 2.0  # 4 beats per measure
        
        measure = int(time // seconds_per_measure) + 1
        beat_time = time % seconds_per_measure
        beat = (beat_time / seconds_per_beat) + 1
        
        return f"{measure}:{beat:.3f}"

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