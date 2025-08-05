import logging
from typing import Optional, Union, Tuple


def get_reapy():
    """Lazy import of reapy."""
    try:
        import reapy
        return reapy
    except ImportError as e:
        logging.error(f"Failed to import reapy: {e}")
        raise


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
                if len(parts) == 2:
                    try:
                        measure = int(parts[0])
                        beat = float(parts[1])
                        return measure_beat_to_time(measure, beat)
                    except ValueError:
                        logging.error(f"Invalid measure:beat format: {position_input}")
                        return None
            
            # Try to parse as float
            try:
                return float(position_input)
            except ValueError:
                logging.error(f"Invalid position format: {position_input}")
                return None
        
        return None
        
    except Exception as e:
        logging.error(f"Failed to parse position {position_input}: {e}")
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
        logging.error(f"Failed to format position {time_seconds}: {e}")
        return f"{time_seconds:.3f}s"


def time_to_measure_beat(time_seconds: float) -> Tuple[int, float, float]:
    """Convert time to measure:beat format."""
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
    """Convert measure:beat format to time in seconds."""
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
