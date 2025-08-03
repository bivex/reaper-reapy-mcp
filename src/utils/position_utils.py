import reapy
from reapy import reascript_api as RPR
from typing import Union

# Constants to replace magic numbers
DEFAULT_BEATS_PER_MEASURE = 4
DEFAULT_BPM = 120.0
SECONDS_PER_MINUTE = 60.0
DEFAULT_SECONDS_PER_BEAT = SECONDS_PER_MINUTE / DEFAULT_BPM
DEFAULT_SECONDS_PER_MEASURE = DEFAULT_SECONDS_PER_BEAT * DEFAULT_BEATS_PER_MEASURE

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
        try:
            measure, beat = map(float, position.split(':'))
            return _convert_measure_beat_to_time(measure, beat, project)
        except ValueError as e:
            raise ValueError(
                f"Invalid measure:beat format: {position}"
            ) from e
        
    return float(position)  # Try direct conversion

def _convert_measure_beat_to_time(measure: float, beat: float, project=None) -> float:
    """Convert measure and beat to time in seconds."""
    if project is None:
        project = reapy.Project()
    
    try:
        # Get project tempo and time signature
        bpm = project.bpm
        beats_per_measure = _get_beats_per_measure(project)
        
        # Calculate time conversion factors
        seconds_per_beat = SECONDS_PER_MINUTE / bpm
        seconds_per_measure = seconds_per_beat * beats_per_measure
        
        # Convert measure:beat to time (measures are 1-based in our interface)
        time = ((measure - 1) * seconds_per_measure + 
                (beat - 1) * seconds_per_beat)
        return time
        
    except Exception as e:
        # Fallback - just return the beat value as seconds
        return beat

def _get_beats_per_measure(project) -> int:
    """Get the number of beats per measure from the project."""
    try:
        time_sig_num, time_sig_den = RPR.TimeMap_GetTimeSigAtTime(project.id, 0)
        if time_sig_num > 0:
            return time_sig_num
    except Exception as e:
        # Use default if getting time signature fails
        pass
    
    return DEFAULT_BEATS_PER_MEASURE

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
        # Get project tempo and time signature
        bpm = project.bpm
        beats_per_measure = _get_beats_per_measure(project)
        
        # Calculate time conversion factors
        seconds_per_beat = SECONDS_PER_MINUTE / bpm
        seconds_per_measure = seconds_per_beat * beats_per_measure
        
        # Convert time to measure:beat
        measure = int(time // seconds_per_measure) + 1  # 1-based measure
        beat_time = time % seconds_per_measure
        beat = (beat_time / seconds_per_beat) + 1  # 1-based beat
        
        return f"{measure}:{beat:.3f}"
        
    except Exception as e:
        # Fallback: estimate based on default values
        return _time_to_measure_fallback(time)

def _time_to_measure_fallback(time: float) -> str:
    """Convert time to measure:beat using default values as fallback."""
    measure = int(time // DEFAULT_SECONDS_PER_MEASURE) + 1
    beat_time = time % DEFAULT_SECONDS_PER_MEASURE
    beat = (beat_time / DEFAULT_SECONDS_PER_BEAT) + 1
    
    return f"{measure}:{beat:.3f}"
