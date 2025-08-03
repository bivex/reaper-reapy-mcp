import reapy
import logging
import os
import re
import time
from typing import List, Dict, Any


class FXController:
    """Controller for FX-related operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def add_fx(self, track_index: int, fx_name: str) -> int:
        """
        Add an FX to a track.
        
        Args:
            track_index (int): Index of the track
            fx_name (str): Name of the FX to add
            
        Returns:
            int: Index of the added FX
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.add_fx(fx_name)
            return fx.index

        except Exception as e:
            self.logger.error(f"Failed to add FX: {e}")
            return -1

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        """
        Remove an FX from a track.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            # Get the FX object first, then remove it
            fx = track.fxs[fx_index]
            fx.delete()
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove FX: {e}")
            return False

    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, value: float) -> bool:
        """
        Set an FX parameter value.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter
            value (float): Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            
            # Try to find parameter by name
            for param_index in range(fx.n_params):
                if fx.params[param_index].name.lower() == param_name.lower():
                    # Store current value for logging
                    try:
                        current_value = fx.params[param_index].value
                    except Exception:
                        current_value = None
                    
                    # Set the new value using multiple approaches
                    try:
                        # Set using reapy's API
                        fx.params[param_index].value = value
                    except Exception as e:
                        self.logger.debug(f"Failed to set parameter via reapy API: {e}")
                    
                    # Also use ReaScript API directly which may be more reliable
                    try:
                        reapy.reascript_api.TrackFX_SetParamNormalized(track.id, fx_index, param_index, value)
                    except Exception as e:
                        self.logger.debug(f"Failed to set parameter via ReaScript API: {e}")
                    
                    # Wait longer for REAPER to update (0.1s instead of 0.01s)
                    time.sleep(0.1)
                    
                    # Verify the change was applied
                    try:
                        new_value = reapy.reascript_api.TrackFX_GetParamNormalized(track.id, fx_index, param_index)
                        self.logger.debug(f"Verified new value is {new_value}")
                    except Exception:
                        pass
                    
                    return True
            
            self.logger.warning(f"FX parameter '{param_name}' not found 1")
            return False
        except Exception as e:
            self.logger.error(f"Failed to set FX parameter: {e}")
            return False

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        """
        Get an FX parameter value.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter
            
        Returns:
            float: Current value of the parameter, or 0.0 if not found
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            
            # Try to find parameter by name
            for param_index in range(fx.n_params):
                if fx.params[param_index].name.lower() == param_name.lower():
                    param = fx.params[param_index]
                    
                    # First try using the ReaScript API directly, which might be more reliable
                    try:
                        # Try to get the normalized value directly from REAPER
                        value = reapy.reascript_api.TrackFX_GetParamNormalized(track.id, fx_index, param_index)
                        if value is not None:
                            return value
                    except Exception:
                        pass
                    
                    # Safely get the parameter value using reapy's API
                    try:
                        value = param.value
                        return value
                    except AttributeError:
                        # If direct access fails, try using get_value() method
                        try:
                            value = param.get_value() if hasattr(param, 'get_value') else 0.0
                            return value
                        except Exception:
                            self.logger.warning(f"Could not get value for parameter {param_name}")
                            return 0.0
            self.logger.warning(f"FX parameter '{param_name}' not found 2")
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to get FX parameter: {e}")
            return 0.0

    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[Dict[str, Any]]:
        """
        Get a list of all parameters for an FX.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            
        Returns:
            List[Dict[str, Any]]: List of parameter information dictionaries
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            
            param_list = []
            for param_index in range(fx.n_params):
                param = fx.params[param_index]
                param_info = {
                    "index": param_index,
                    "name": param.name
                }
                
                # Safely get parameter value using exception handling
                try:
                    param_info["value"] = param.value
                except AttributeError:
                    # If direct value access fails, try using get_value() method
                    try:
                        param_info["value"] = param.get_value() if hasattr(param, 'get_value') else 0.0
                    except Exception:
                        # As a fallback, provide a default value
                        param_info["value"] = 0.0
                        self.logger.warning(f"Could not get value for parameter {param.name}")
                
                # Safely get formatted value
                try:
                    param_info["formatted_value"] = param.formatted_value if hasattr(param, 'formatted_value') else str(param_info["value"])
                except Exception:
                    param_info["formatted_value"] = str(param_info["value"])
                
                param_list.append(param_info)
                
            self.logger.info(f"Retrieved {len(param_list)} parameters for FX {fx.name}")
            return param_list

        except Exception as e:
            self.logger.error(f"Failed to get FX parameter list: {e}")
            return []

    def get_fx_list(self, track_index: int) -> List[Dict[str, Any]]:
        """
        Get a list of all FX on a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            List[Dict[str, Any]]: List of FX information dictionaries
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            fx_list = []
            for fx_index, fx in enumerate(track.fxs):
                fx_info = {
                    "index": fx_index,
                    "name": fx.name,
                    "enabled": fx.enabled if hasattr(fx, 'enabled') else True
                }
                fx_list.append(fx_info)
            
            self.logger.info(f"Retrieved {len(fx_list)} FX for track {track_index}")
            return fx_list

        except Exception as e:
            self.logger.error(f"Failed to get FX list: {e}")
            return []

    def get_available_fx_list(self) -> List[str]:
        """
        Get a list of all available FX plugins in Reaper by reading Reaper's INI files
        and using reapy's API functions.
        
        Returns:
            List[str]: List of available FX names
        """
        try:
            fx_list = []
            
            # Try to find and read Reaper's reaper-plugs.ini file
            try:
                self.logger.info("Attempting to read Reaper plugin database files")
                # Determine likely locations for Reaper's config files
                reaper_resource_paths = []
                
                # Check common Windows locations
                appdata = os.environ.get('APPDATA')
                if appdata:
                    reaper_resource_paths.append(os.path.join(appdata, 'REAPER'))
                
                # Check if ReaperResourcePath is available through reapy
                try:
                    resource_path = reapy.reascript_api.GetResourcePath()
                    if resource_path:
                        reaper_resource_paths.append(resource_path)
                except Exception as e:
                    self.logger.warning(f"Failed to get Reaper resource path: {e}")
                
                # Try to find and read the plugin database files
                for resource_path in reaper_resource_paths:
                    self.logger.info(f"Checking resource path: {resource_path}")
                    plugin_ini_files = ['reaper-plugs.ini', 'reaper-plugs64.ini', 'reaper-vstplugins.ini', 'reaper-vstplugins64.ini']
                    
                    for ini_file in plugin_ini_files:
                        ini_path = os.path.join(resource_path, ini_file)
                        if os.path.exists(ini_path):
                            self.logger.info(f"Found plugin database at: {ini_path}")
                            # Read the file and parse it for plugin names
                            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line in f:
                                    # Plugin entries typically contain an equals sign
                                    if '=' in line:
                                        parts = line.strip().split('=')
                                        if len(parts) > 1:
                                            right_part = parts[1]
                                            
                                            # Try to extract names in the format: dll=ID,number,PluginName
                                            # Example: reacast.dll=00EF6D73D190DA01,1919246691,ReaCast (Cockos)
                                            if ',' in right_part:
                                                comma_parts = right_part.split(',')
                                                if len(comma_parts) >= 3:
                                                    # The plugin name is typically after the second comma
                                                    plugin_name = comma_parts[2].strip()
                                                    if plugin_name and plugin_name not in fx_list:
                                                        fx_list.append(plugin_name)
                                                        continue  # Skip other checks for this line
                                            
                                            # Also try the old method for other formats
                                            # Sometimes plugin names are in quotes
                                            for part in parts:
                                                if part.strip() and '"' in part:
                                                    # Extract the name within quotes
                                                    name_match = re.search(r'"([^"]+)"', part)
                                                    if name_match:
                                                        plugin_name = name_match.group(1)
                                                        if plugin_name not in fx_list:
                                                            fx_list.append(plugin_name)
            except Exception as e:
                self.logger.warning(f"Failed to read Reaper plugin database: {e}")
            
            # Deduplicate and sort the list
            if fx_list:
                unique_fx_list = sorted(list(set(fx_list)))
                self.logger.info(f"Retrieved {len(unique_fx_list)} unique FX plugins")
                return unique_fx_list
            else:
                self.logger.warning("No FX plugins found through any method")
                return []

        except Exception as e:
            self.logger.error(f"Failed to get available FX list: {e}")
            return []

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool = None) -> bool:
        """
        Toggle or set the enable/disable state of an FX.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            enable (bool, optional): True to enable, False to disable, None to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            if enable is None:
                fx.enabled = not fx.enabled
            else:
                fx.enabled = enable
            return True

        except Exception as e:
            self.logger.error(f"Failed to toggle FX: {e}")
            return False
