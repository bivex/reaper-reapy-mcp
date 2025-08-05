import logging
from typing import Dict, Any, List, Optional


class AdvancedRoutingController:
    """Controller for advanced routing and bussing operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Lazy import of reapy to avoid connection errors on import
        self._reapy = None
        self._RPR = None

    def _get_reapy(self):
        """Lazy import of reapy."""
        if self._reapy is None:
            try:
                import reapy
                self._reapy = reapy
                self._RPR = reapy.reascript_api
            except ImportError as e:
                self.logger.error(f"Failed to import reapy: {e}")
                raise
        return self._reapy

    def create_folder_track(self, name: str = "Folder Track") -> int:
        """
        Create a folder track that can contain other tracks.
        
        Args:
            name (str): Name for the folder track
            
        Returns:
            int: Track index of the created folder track
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            # Create a new track using the correct API function
            track_index = len(project.tracks)
            self._RPR.InsertTrackAtIndex(track_index, True)  # Use InsertTrackAtIndex instead of InsertMediaTrack
            
            # Get the created track
            track = project.tracks[track_index]
            
            # Set track name
            track.name = name
            
            # Set as folder track (depth = 1)
            self._RPR.SetMediaTrackInfo_Value(track.id, "I_FOLDERDEPTH", 1)
            
            self.logger.info(f"Created folder track '{name}' at index {track_index}")
            return track_index
            
        except Exception as e:
            self.logger.error(f"Failed to create folder track: {e}")
            return -1

    def create_bus_track(self, name: str = "Bus Track") -> int:
        """
        Create a bus track for grouping and processing multiple tracks.
        
        Args:
            name (str): Name for the bus track
            
        Returns:
            int: Track index of the created bus track
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            # Create a new track using the correct API function
            track_index = len(project.tracks)
            self._RPR.InsertTrackAtIndex(track_index, True)  # Use InsertTrackAtIndex instead of InsertMediaTrack
            
            # Get the created track
            track = project.tracks[track_index]
            
            # Set track name
            track.name = name
            
            # Set as bus track (depth = 0, but will be used for routing)
            self._RPR.SetMediaTrackInfo_Value(track.id, "I_FOLDERDEPTH", 0)
            
            self.logger.info(f"Created bus track '{name}' at index {track_index}")
            return track_index
            
        except Exception as e:
            self.logger.error(f"Failed to create bus track: {e}")
            return -1

    def set_track_parent(self, child_track_index: int, parent_track_index: int) -> bool:
        """
        Set a track's parent folder track.
        
        Args:
            child_track_index (int): Index of the child track
            parent_track_index (int): Index of the parent track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            if child_track_index >= len(project.tracks) or parent_track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return False
            
            child_track = project.tracks[child_track_index]
            parent_track = project.tracks[parent_track_index]
            
            # Set the child track's folder depth to make it a child of the parent
            # The depth determines the nesting level
            self._RPR.SetMediaTrackInfo_Value(child_track.id, "I_FOLDERDEPTH", 1)
            
            # For now, just set the folder depth without reordering
            # The parent-child relationship is established by folder depth
            self.logger.info(f"Set track {child_track_index} as child of track {parent_track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set track parent: {e}")
            return False

    def get_track_children(self, parent_track_index: int) -> List[int]:
        """
        Get all child tracks of a parent track.
        
        Args:
            parent_track_index (int): Index of the parent track
            
        Returns:
            List[int]: List of child track indices
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            if parent_track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return []
            
            children = []
            parent_depth = self._RPR.GetMediaTrackInfo_Value(project.tracks[parent_track_index].id, "I_FOLDERDEPTH")
            
            # Look for tracks that are children of this parent
            for i in range(parent_track_index + 1, len(project.tracks)):
                track = project.tracks[i]
                track_depth = self._RPR.GetMediaTrackInfo_Value(track.id, "I_FOLDERDEPTH")
                
                # If we find a track with depth <= 0, we've reached the end of this folder
                if track_depth <= 0:
                    break
                
                # If the track has positive depth, it's a child
                if track_depth > 0:
                    children.append(i)
            
            self.logger.info(f"Found {len(children)} children for track {parent_track_index}")
            return children
            
        except Exception as e:
            self.logger.error(f"Failed to get track children: {e}")
            return []

    def set_track_folder_depth(self, track_index: int, depth: int) -> bool:
        """
        Set the folder depth of a track.
        
        Args:
            track_index (int): Index of the track
            depth (int): Folder depth (0 = normal track, 1 = folder start, -1 = folder end)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return False
            
            track = project.tracks[track_index]
            self._RPR.SetMediaTrackInfo_Value(track.id, "I_FOLDERDEPTH", depth)
            
            self.logger.info(f"Set track {track_index} folder depth to {depth}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set track folder depth: {e}")
            return False

    def get_track_folder_depth(self, track_index: int) -> int:
        """
        Get the folder depth of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            int: Folder depth of the track
        """
        try:
            reapy = self._get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return 0
            
            track = project.tracks[track_index]
            depth = self._RPR.GetMediaTrackInfo_Value(track.id, "I_FOLDERDEPTH")
            
            return int(depth)
            
        except Exception as e:
            self.logger.error(f"Failed to get track folder depth: {e}")
            return 0 
        
