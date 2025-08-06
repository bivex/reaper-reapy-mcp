import logging
from typing import Optional, Union
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy


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
            reapy = get_reapy()

            # Try to connect to REAPER first with connection retry
            from constants import TEMPO_DECIMAL_PLACES

            max_retries = TEMPO_DECIMAL_PLACES
            for attempt in range(max_retries):
                try:
                    project = reapy.Project()

                    # Log the current state for debugging
                    self.logger.info(
                        f"Setting tempo to {bpm} BPM (attempt {attempt + 1})"
                    )

                    # Try to set the tempo
                    project.bpm = float(bpm)

                    # Verify the tempo was set correctly
                    new_tempo = project.bpm
                    self.logger.info(f"Tempo set successfully. New tempo: {new_tempo}")

                    return True

                except (ConnectionAbortedError, ConnectionError) as ce:
                    self.logger.warning(
                        f"Connection error on attempt {attempt + 1}: {ce}"
                    )
                    if attempt == max_retries - 1:
                        raise ce
                    # Wait a bit before retrying
                    import time

                    time.sleep(0.1)
                    continue

        except AttributeError as e:
            error_message = f"Failed to set tempo to {bpm}: Attribute error - {e}"
            self.logger.error(error_message)
            return False
        except (ConnectionAbortedError, ConnectionError) as ce:
            error_message = f"Failed to set tempo to {bpm}: Connection error - {ce}"
            self.logger.error(error_message)
            return False
        except Exception as e:
            error_message = f"Failed to set tempo to {bpm}: {type(e).__name__}: {e}"
            self.logger.error(error_message)
            return False

    def get_tempo(self) -> Optional[float]:
        """
        Get the current project tempo.

        Returns:
            float: Current tempo in beats per minute, or None if not available
        """
        try:
            reapy = get_reapy()

            # Try to connect to REAPER first with connection retry
            from constants import TEMPO_DECIMAL_PLACES

            max_retries = TEMPO_DECIMAL_PLACES
            for attempt in range(max_retries):
                try:
                    project = reapy.Project()
                    tempo = project.bpm
                    self.logger.info(f"Current tempo: {tempo} BPM")
                    return tempo

                except (ConnectionAbortedError, ConnectionError) as ce:
                    self.logger.warning(
                        f"Connection error on attempt {attempt + 1}: {ce}"
                    )
                    if attempt == max_retries - 1:
                        raise ce
                    # Wait a bit before retrying
                    import time

                    time.sleep(0.1)
                    continue

        except (ConnectionAbortedError, ConnectionError) as ce:
            error_message = f"Failed to get tempo: Connection error - {ce}"
            self.logger.error(error_message)
            return None
        except Exception as e:
            error_message = f"Failed to get tempo: {type(e).__name__}: {e}"
            self.logger.error(error_message)
            return None

    def clear_project(self) -> bool:
        """
        Clear all items from all tracks in the project.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
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
