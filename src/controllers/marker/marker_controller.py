import logging
from typing import List, Dict, Any, Optional


import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy


class MarkerController:
    """Controller for marker and region operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
    def add_marker(self, position: float, name: str = "") -> bool:
        """
        Add a marker at the specified position.
        
        Args:
            position (float): Position in seconds
            name (str): Name of the marker
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            # Add marker using ReaScript API
            marker_id = self._RPR.AddProjectMarker2(project.id, False, position, 0, name, -1, 0)
            return marker_id >= 0

        except Exception as e:
            error_message = f"Failed to add marker at position {position}: {e}"
            self.logger.error(error_message)
            return False

    def get_markers(self) -> List[Dict[str, Any]]:
        """
        Get all markers in the project.
        
        Returns:
            List[Dict[str, Any]]: List of marker information
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            markers = []
            marker_count = self._RPR.CountProjectMarkers(project.id)[0]
            
            for i in range(marker_count):
                marker_info = self._RPR.EnumProjectMarkers2(project.id, i)
                if marker_info and marker_info[1]:  # Check if it's a marker (not region)
                    markers.append({
                        'id': i,
                        'position': marker_info[2],
                        'name': marker_info[4],
                        'color': marker_info[5]
                    })
            
            return markers

        except Exception as e:
            self.logger.error(f"Failed to get markers: {e}")
            return []

    def create_region(self, start_time: float, end_time: float, name: str) -> int:
        """
        Create a region in the project.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            name (str): Name of the region
            
        Returns:
            int: Index of the created region
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            region = project.add_region(start_time, end_time, name)
            return region.index
        except Exception as e:
            error_message = f"Failed to create region: {e}"
            self.logger.error(error_message)
            return -1

    def delete_region(self, region_index: int) -> bool:
        """
        Delete a region from the project.
        
        Args:
            region_index (int): Index of the region to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:                
            reapy = get_reapy()
            project = reapy.Project()
            
            # Log all region indices for debugging
            region_indices = [r.index for r in project.regions]
            self.logger.debug(f"Available region indices: {region_indices}")
            self.logger.debug(f"Attempting to delete region with index: {region_index}")
            
            # Try to find the region by index - first with exact match
            for region in project.regions:
                if region.index == region_index:
                    region.delete()
                    self.logger.info(f"Deleted region with index {region_index}")
                    return True
            
            # If not found, try with string comparison
            str_region_index = str(region_index)
            for region in project.regions:
                if str(region.index) == str_region_index:
                    region.delete()
                    self.logger.info(f"Deleted region with string index match {region_index}")
                    return True
            
            # If still not found, use ReaScript API directly
            try:
                # Try to delete using ReaScript API
                reapy = get_reapy()
                RPR = reapy.reascript_api
                result = RPR.DeleteProjectMarker(0, region_index, True)  # isRegion=True
                if result:
                    self.logger.info(
                        f"Deleted region using ReaScript API {region_index}"
                    )
                    return True
            except Exception as e:
                self.logger.warning(
                    f"Failed to delete region with ReaScript API: {e}"
                )
                
            # As a fallback, try the project's method
            try:
                # Try to delete by index directly
                project.delete_region_by_index(region_index)
                self.logger.info(f"Deleted region using delete_region_by_index {region_index}")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to delete region with delete_region_by_index: {e}")
            
            self.logger.error(f"Could not find region with index {region_index}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete region: {e}")
            return False

    def create_marker(self, time: float, name: str) -> int:
        """
        Create a marker in the project.
        
        Args:
            time (float): Time position in seconds
            name (str): Name of the marker
            
        Returns:
            int: Index of the created marker
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            marker = project.add_marker(time, name)
            return marker.index
        except Exception as e:
            error_message = f"Failed to create marker: {e}"
            self.logger.error(error_message)
            return -1

    def delete_marker(self, marker_index: int) -> bool:
        """
        Delete a marker from the project.
        
        Args:
            marker_index (int): Index of the marker to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try: 
            reapy = get_reapy()
            project = reapy.Project()
            
            # Log all marker indices for debugging
            marker_indices = [m.index for m in project.markers]
            self.logger.debug(
                f"Available marker indices: {marker_indices}"
            )
            self.logger.debug(
                f"Attempting to delete marker with index: {marker_index}"
            )
            
            # First try direct access with safer index checking
            try:
                markers_list = list(project.markers)
                if markers_list and 0 <= marker_index < len(markers_list):
                    marker = markers_list[marker_index]
                    marker.delete()
                    self.logger.info(f"Deleted marker with direct access: {marker_index}")
                    return True
            except Exception as e:
                self.logger.warning(f"Could not delete marker with direct access: {e}")
            
            # If direct access fails, try to find by index property
            for marker in project.markers:
                if marker.index == marker_index:
                    marker.delete()
                    self.logger.info(f"Deleted marker with index matching: {marker_index}")
                    return True
            
            # Try string comparison
            str_marker_index = str(marker_index)
            for marker in project.markers:
                if str(marker.index) == str_marker_index:
                    marker.delete()
                    self.logger.info(f"Deleted marker with string index matching: {marker_index}")
                    return True
            
            self.logger.error(f"Could not find marker with index {marker_index}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete marker: {e}")
            return False
