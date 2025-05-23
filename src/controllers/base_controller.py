import reapy
import logging
import os
import re
import time
from typing import Optional, List, Dict, Any, Union, Tuple

class BaseController:
    """Base controller for interacting with Reaper using reapy."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the Reaper controller.
        
        Args:
            debug (bool): Enable debug logging
        """
        self.logger = logging.getLogger(__name__)
        self.debug = debug
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Initialize test data storage for storing MIDI notes during testing
        self._test_midi_items = {}
        
        # Connect to Reaper
        try:
            reapy.connect()
            self.logger.info("Connected to Reaper")
        except Exception as e:
            self.logger.error(f"Failed to connect to Reaper: {e}")
            raise

    def verify_connection(self) -> bool:
        """Verify connection to Reaper."""
        try:
            project = reapy.Project()
            print("Connected to project:", project.name)
            # TODO correct checker
            # return reapy.is_connected()
            return True
        except Exception as e:
            self.logger.error(f"Connection verification failed: {e}")
            return False

    def _validate_track_index(self, track_index: int) -> bool:
        """
        Validate that a track index is within valid range.
        
        Args:
            track_index (int): The track index to validate
            
        Returns:
            bool: True if valid, False if invalid
        """
        try:
            track_index = int(track_index)
            if track_index < 0:
                return False
                
            project = reapy.Project()
            num_tracks = len(project.tracks)
            return track_index < num_tracks
        except Exception:
            return False
            
    def _get_track(self, track_index: int) -> Optional[reapy.Track]:
        """
        Get a track by index with validation.
        
        Args:
            track_index (int): The track index to get
            
        Returns:
            Optional[reapy.Track]: The track if valid, None if invalid
        """
        if not self._validate_track_index(track_index):
            return None
            
        try:
            return reapy.Project().tracks[track_index]
        except Exception:
            return None
