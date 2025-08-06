"""
Time and position conversion utilities for REAPER projects.
Provides functionality for converting between time formats (seconds, measure:beat)
and accessing project time map information.
"""
import logging
from typing import Optional, Union, Tuple, Dict

from ..core.reapy_bridge import get_reapy, get_rpr

logger = logging.getLogger(__name__)

# Constants to replace magic numbers
DEFAULT_BPM = 120.0
DEFAULT_TIME_SIG_NUM = 4
DEFAULT_TIME_SIG_DEN = 4


def parse_position(position_input: Union[str, float]) -> Optional[float]:
    """
    Parse position input that can be either time in seconds or measure:beat format.
    
    Args:
        position_input (Union[str, float]): Position as time (float) or measure:beat (str)
        
    Returns:
        Optional[float]: Time in seconds, or None if parsing fails
    """
    try:
        if isinstance(position_input, (int, float)):
            return float(position_input)
        
        if isinstance(position_input, str):
            # Check if it's in measure:beat format
            if ':' in position_input:
                parts = position_input.split(':')
                from constants import POSITION_COMPONENTS_COUNT
                if len(parts) == POSITION_COMPONENTS_COUNT:
                    try:
                        measure = int(parts[0])
                        beat = float(parts[1])
                        return measure_beat_to_time(measure, beat)
                    except ValueError:
                        logger.error(f"Invalid measure:beat format: {position_input}")
                        return None
            
            # Try to parse as float
            try:
                return float(position_input)
            except ValueError:
                logger.error(f"Invalid position format: {position_input}")
                return None
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to parse position {position_input}: {e}")
        return None


def format_position(time_seconds: float, format_type: str = "time") -> str:
    """
    Format time in seconds to different formats.
    
    Args:
        time_seconds (float): Time in seconds
        format_type (str): Format type ("time", "measure:beat", "both")
        
    Returns:
        str: Formatted position string
    """
    try:
        if format_type == "time":
            return f"{time_seconds:.3f}s"
        elif format_type == "measure:beat":
            measure, beat, _ = time_to_measure_beat(time_seconds)
            return f"{measure}:{beat:.2f}"
        elif format_type == "both":
            measure, beat, _ = time_to_measure_beat(time_seconds)
            return f"{time_seconds:.3f}s ({measure}:{beat:.2f})"
        else:
            return f"{time_seconds:.3f}s"
            
    except Exception as e:
        logger.error(f"Failed to format position {time_seconds}: {e}")
        return f"{time_seconds:.3f}s"


def time_to_measure_beat(time_seconds: float) -> Tuple[int, float, float]:
    """
    Convert time in seconds to measure:beat format.
    
    Args:
        time_seconds (float): Time in seconds
        
    Returns:
        Tuple[int, float, float]: (measure, beat, beat_fraction)
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        
        # Get time signature info
        time_signature = project.time_signature
        beats_per_measure = time_signature[0] / time_signature[1]
        
        # Convert time to beats
        from constants import SECONDS_PER_MINUTE
        beats = time_seconds * project.tempo / SECONDS_PER_MINUTE
        
        # Calculate measure and beat
        measure = int(beats / beats_per_measure) + 1
        beat = (beats % beats_per_measure) + 1
        beat_fraction = beat - int(beat)
        
        return measure, int(beat), beat_fraction
        
    except Exception as e:
        logger.error(f"Failed to convert time to measure:beat: {e}")
        return 1, 1, 0.0


def measure_beat_to_time(measure: int, beat: float) -> float:
    """
    Convert measure:beat format to time in seconds.
    
    Args:
        measure (int): Measure number (1-based)
        beat (float): Beat within the measure (1-based)
        
    Returns:
        float: Time in seconds
    """
    try:
        reapy = get_reapy()
        project = reapy.Project()
        
        # Get time signature info
        time_signature = project.time_signature
        beats_per_measure = time_signature[0] / time_signature[1]
        
        # Calculate total beats
        total_beats = (measure - 1) * beats_per_measure + (beat - 1)
        
        # Convert beats to time
        from constants import SECONDS_PER_MINUTE
        time_seconds = total_beats * SECONDS_PER_MINUTE / project.tempo
        
        return time_seconds
        
    except Exception as e:
        logger.error(f"Failed to convert measure:beat to time: {e}")
        return 0.0


def get_time_map_info(project=None) -> Dict[str, Union[float, int]]:
    """
    Get time map information for the project, including BPM,
    time signature numerator, and time signature denominator.
    
    Args:
        project: Optional project instance. If None, uses current project.
        
    Returns:
        Dict containing 'bpm', 'time_sig_num', and 'time_sig_den'
    """
    try:
        reapy = get_reapy()
        if project is None:
            project = reapy.Project()
        
        # Get time signature at current cursor
        rpr = get_rpr()
        time_sig_num, time_sig_den = rpr.TimeMap_GetTimeSigAtTime(project.id, 0)
        
        return {
            'bpm': project.bpm,
            'time_sig_num': time_sig_num,
            'time_sig_den': time_sig_den
        }
    except Exception as e:
        # Log the error and return defaults if getting info fails
        logger.warning(f"Failed to get time map info from project: {e}. Using default values.")
        return _get_default_time_map_info()


def _get_default_time_map_info() -> Dict[str, Union[float, int]]:
    """Get default time map information."""
    return {
        'bpm': DEFAULT_BPM,
        'time_sig_num': DEFAULT_TIME_SIG_NUM,
        'time_sig_den': DEFAULT_TIME_SIG_DEN
    }