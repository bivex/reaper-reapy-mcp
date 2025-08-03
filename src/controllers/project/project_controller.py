import reapy
import logging
from typing import Optional, Union


class ProjectController:
    """Controller for project-level operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
    
    def set_tempo(self, bpm: float) -> bool:
        """
        Set the project tempo.
        
        Args:
            bpm (float): Tempo in beats per minute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            project.bpm = float(bpm)
            return True
            
        except Exception as e:
            error_message = f"Failed to set tempo to {bpm}: {e}"
            self.logger.error(error_message)
            return False
    
    def get_tempo(self) -> Optional[float]:
        """
        Get the current project tempo.
        
        Returns:
            float: Current tempo in beats per minute, or None if not available
        """
        try:
            project = reapy.Project()
            return project.bpm
            
        except Exception as e:
            error_message = f"Failed to get tempo: {e}"
            self.logger.error(error_message)
            return None

    def clear_project(self) -> bool:
        """
        Clear all items from all tracks in the project.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            
            # Clear all items from all tracks
            for track in project.tracks:
                # Get all items on this track
                items_to_delete = list(track.items)  # Create a copy of the list
                
                # Delete each item
                for item in items_to_delete:
                    item.delete()
            
            self.logger.info("Cleared all items from project")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear project: {e}")
            return False
