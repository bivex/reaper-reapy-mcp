import logging
from typing import Optional, Tuple, Dict


def get_reapy():
    """Lazy import of reapy."""
    try:
        import reapy
        return reapy
    except ImportError as e:
        logging.error(f"Failed to import reapy: {e}")
        raise


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
        beats = time_seconds * project.tempo / 60.0
        
        # Calculate measure and beat
        measure = int(beats / beats_per_measure) + 1
        beat = (beats % beats_per_measure) + 1
        beat_fraction = beat - int(beat)
        
        return measure, int(beat), beat_fraction
        
    except Exception as e:
        logging.error(f"Failed to convert time to measure:beat: {e}")
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
        time_seconds = total_beats * 60.0 / project.tempo
        
        return time_seconds
        
    except Exception as e:
        logging.error(f"Failed to convert measure:beat to time: {e}")
        return 0.0

# Set up logging
logger = logging.getLogger(__name__)

# Constants to replace magic numbers
DEFAULT_BPM = 120.0
DEFAULT_TIME_SIG_NUM = 4
DEFAULT_TIME_SIG_DEN = 4

def get_time_map_info(project=None) -> dict:
    """
    Get time map information for the project, including BPM,
    time signature numerator, and time signature denominator.
    """
    try:
        reapy = get_reapy()
        if project is None:
            project = reapy.Project()
        
        # Get time signature at current cursor
        RPR = reapy.reascript_api
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
