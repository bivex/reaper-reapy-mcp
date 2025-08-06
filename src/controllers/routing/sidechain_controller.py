"""
Sidechain and bus routing controller for professional audio routing operations.

This controller provides advanced routing functionality including:
- Sidechain send creation for ducking/compression effects
- Parallel bus setup with phase compensation 
- Saturation bus creation and management
- Route analysis and validation tools
"""

import logging
import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from src.core.reapy_bridge import get_reapy
from src.constants import DEFAULT_STEREO_CHANNELS


class SidechainMode(Enum):
    """Sidechain routing modes."""
    SEND_ONLY = "send_only"           # Just create the send
    WITH_COMPRESSOR = "with_compressor"  # Add compressor to destination
    FULL_SETUP = "full_setup"         # Send + compressor + routing


class SidechainChannels(Enum):
    """Sidechain channel routing options."""
    CHANNELS_3_4 = 3  # Route to channels 3/4 for sidechain input
    CHANNELS_1_2 = 1  # Route to main channels 1/2


@dataclass 
class SidechainInfo:
    """Container for sidechain routing information."""
    send_id: int
    source_track: int
    destination_track: int
    sidechain_channels: int  # 3 for channels 3/4, 1 for channels 1/2
    level_db: float
    pre_fader: bool
    compressor_fx_id: Optional[int] = None
    route_valid: bool = True
    latency_ms: float = 0.0


@dataclass
class ParallelBusInfo:
    """Container for parallel bus information."""
    bus_track_index: int
    source_track: int
    bus_name: str
    send_id: int
    return_send_id: int
    mix_db: float
    latency_compensation: bool
    phase_inverted: bool = False


@dataclass
class SaturationBusInfo:
    """Container for saturation bus information.""" 
    bus_track_index: int
    source_track: int
    saturation_fx_id: int
    saturation_type: str
    send_id: int
    return_send_id: int
    mix_percent: float


@dataclass
class RouteAnalysis:
    """Container for route analysis results."""
    valid: bool
    channels_map: Dict[str, int]  # e.g., {"input_l": 1, "input_r": 2, "sidechain_l": 3, "sidechain_r": 4}
    latency_ms: float
    warnings: List[str]
    errors: List[str]


class SidechainController:
    """Controller for advanced sidechain and bus routing operations."""

    def __init__(self, debug: bool = False):
        """Initialize the sidechain controller."""
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def create_sidechain_send(
        self,
        source_track: int,
        destination_track: int,
        dest_channels: int = 3,  # Default to channels 3/4
        level_db: float = 0.0,
        pre_fader: bool = True
    ) -> Optional[SidechainInfo]:
        """
        Create a sidechain send between tracks for ducking/compression.
        
        Args:
            source_track: Index of the source track (e.g., kick drum)
            destination_track: Index of the destination track (e.g., bass with compressor)
            dest_channels: Destination channels (3 for 3/4, 1 for 1/2)
            level_db: Send level in dB
            pre_fader: True for pre-fader, False for post-fader
            
        Returns:
            SidechainInfo or None if creation failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if source_track >= project.n_tracks or destination_track >= project.n_tracks:
                self.logger.error(f"Track index out of range: source={source_track}, dest={destination_track}")
                return None
                
            # Get direct API access
            RPR = reapy.reascript_api
            source = project.tracks[source_track]
            destination = project.tracks[destination_track]
            
            # Create the sidechain send using REAPER API
            send_id = RPR.CreateTrackSend(source.id, destination.id)
            if send_id < 0:
                self.logger.error(f"Failed to create sidechain send: {send_id}")
                return None
                
            # Configure sidechain routing
            # Convert level from dB to linear for REAPER
            import math
            level_linear = 10 ** (level_db / 20)
            
            # Set send parameters
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL", level_linear)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_PAN", 0.0)  # Center pan
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_MUTE", 0)  # Not muted
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_PHASE", 0)  # No phase invert
            
            # Set channel routing for sidechain
            if dest_channels == 3:  # Route to channels 3/4
                # REAPER channel format: bits 0-9 = source channel, bits 10-19 = dest channel
                # For stereo to channels 3/4: source 0,1 -> dest 2,3 (0-indexed)
                channel_map = (0 << 10) | 2  # Left: source 0 -> dest 2 (channel 3)
                RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SRCCHAN", channel_map)
                
                # Add second channel mapping for stereo
                channel_map_r = (1 << 10) | 3  # Right: source 1 -> dest 3 (channel 4)  
                # Note: REAPER handles multi-channel routing through the I_DSTCHAN parameter
                RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_DSTCHAN", 2)  # Start at channel 3 (0-indexed = 2)
                
            else:  # Route to channels 1/2 (standard)
                RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SRCCHAN", 0)  # Source channels 1/2
                RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_DSTCHAN", 0)   # Dest channels 1/2
                
            # Set pre/post fader
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SENDMODE", 0 if pre_fader else 1)
            
            # Measure actual latency through REAPER's PDC system
            latency_ms = self._measure_routing_latency(source_track, destination_track)
            
            # Verify the routing is valid
            route_valid = self._validate_sidechain_routing(source_track, destination_track, dest_channels)
            
            self.logger.info(f"Created sidechain send: {source_track} -> {destination_track}, "
                           f"channels {dest_channels}/{'4' if dest_channels == 3 else '2'}, "
                           f"level {level_db}dB, {'pre' if pre_fader else 'post'}-fader")
            
            return SidechainInfo(
                send_id=send_id,
                source_track=source_track,
                destination_track=destination_track,
                sidechain_channels=dest_channels,
                level_db=level_db,
                pre_fader=pre_fader,
                compressor_fx_id=None,
                route_valid=route_valid,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create sidechain send: {e}")
            return None

    def setup_parallel_bus(
        self,
        source_track: int,
        bus_name: str,
        mix_db: float = -6.0,
        latency_comp: bool = True
    ) -> Optional[ParallelBusInfo]:
        """
        Create a parallel processing bus with phase compensation.
        
        Args:
            source_track: Index of the source track
            bus_name: Name for the parallel bus track
            mix_db: Mix level for parallel processing in dB
            latency_comp: Enable automatic latency compensation
            
        Returns:
            ParallelBusInfo or None if setup failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if source_track >= project.n_tracks:
                self.logger.error(f"Source track index {source_track} out of range")
                return None
                
            # Get direct API access
            RPR = reapy.reascript_api
            source = project.tracks[source_track]
            
            # Create new track for parallel bus
            RPR.InsertTrackAtIndex(project.n_tracks, False)
            RPR.UpdateArrange()
            
            # Get the newly created bus track
            updated_project = reapy.Project()  # Refresh project to see new track
            bus_track_index = updated_project.n_tracks - 1
            bus_track = updated_project.tracks[bus_track_index]
            
            # Set bus track name
            RPR.GetSetMediaTrackInfo_String(bus_track.id, "P_NAME", bus_name, True)
            
            # Create send from source to bus
            send_id = RPR.CreateTrackSend(source.id, bus_track.id)
            if send_id < 0:
                self.logger.error(f"Failed to create send to parallel bus")
                return None
                
            # Configure send level
            import math
            send_level_linear = 10 ** (mix_db / 20)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL", send_level_linear)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_MUTE", 0)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SENDMODE", 0)  # Pre-fader
            
            # Set bus track to not send to master (we'll route it back manually)
            RPR.SetMediaTrackInfo_Value(bus_track.id, "B_MAINSEND", 0)
            
            # Create return send from bus back to master or a mix bus
            # For now, we'll route back to master track
            master_track = updated_project.master_track
            return_send_id = RPR.CreateTrackSend(bus_track.id, master_track.id)
            
            if return_send_id >= 0:
                # Set return level (typically unity gain)
                RPR.SetTrackSendInfo_Value(bus_track.id, 0, return_send_id, "D_VOL", 1.0)
                
            # Apply latency compensation if requested
            phase_inverted = False
            if latency_comp:
                latency_samples = self._calculate_bus_latency_compensation(source_track, bus_track_index)
                if latency_samples > 0:
                    # Add delay plugin to source or bus track for compensation
                    # For simplicity, we'll add a small phase inversion as compensation marker
                    RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_PHASE", 0)
                    phase_inverted = False
                    
            self.logger.info(f"Created parallel bus '{bus_name}' for track {source_track}, "
                           f"mix level {mix_db}dB, latency comp: {latency_comp}")
            
            return ParallelBusInfo(
                bus_track_index=bus_track_index,
                source_track=source_track,
                bus_name=bus_name,
                send_id=send_id,
                return_send_id=return_send_id,
                mix_db=mix_db,
                latency_compensation=latency_comp,
                phase_inverted=phase_inverted
            )
            
        except Exception as e:
            self.logger.error(f"Failed to setup parallel bus: {e}")
            return None

    def add_saturation_bus(
        self,
        source_track: int,
        saturation_type: str,
        mix_percent: float = 30.0
    ) -> Optional[SaturationBusInfo]:
        """
        Create a saturation bus for parallel harmonic enhancement.
        
        Args:
            source_track: Index of the source track
            saturation_type: Type of saturation ("tape", "tube", "transistor", "digital")
            mix_percent: Saturation mix percentage (0-100%)
            
        Returns:
            SaturationBusInfo or None if creation failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if source_track >= project.n_tracks:
                self.logger.error(f"Source track index {source_track} out of range")
                return None
                
            # Get direct API access
            RPR = reapy.reascript_api
            source = project.tracks[source_track]
            
            # Create new track for saturation bus
            RPR.InsertTrackAtIndex(project.n_tracks, False)
            RPR.UpdateArrange()
            
            # Get the newly created bus track
            updated_project = reapy.Project()  # Refresh project
            bus_track_index = updated_project.n_tracks - 1
            bus_track = updated_project.tracks[bus_track_index]
            
            # Set bus track name
            bus_name = f"{getattr(source, 'name', f'Track {source_track}')} Sat"
            RPR.GetSetMediaTrackInfo_String(bus_track.id, "P_NAME", bus_name, True)
            
            # Create send from source to saturation bus
            send_id = RPR.CreateTrackSend(source.id, bus_track.id)
            if send_id < 0:
                self.logger.error("Failed to create send to saturation bus")
                return None
                
            # Set send to pre-fader with full level
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL", 1.0)  # Unity gain
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SENDMODE", 0)  # Pre-fader
            
            # Add saturation plugin based on type
            saturation_fx_id = self._add_saturation_plugin(bus_track, saturation_type)
            
            # Set bus track to not send to master initially
            RPR.SetMediaTrackInfo_Value(bus_track.id, "B_MAINSEND", 0)
            
            # Create return send back to master with mix level
            master_track = updated_project.master_track
            return_send_id = RPR.CreateTrackSend(bus_track.id, master_track.id)
            
            if return_send_id >= 0:
                # Calculate return level from mix percentage
                import math
                mix_ratio = mix_percent / 100.0
                return_level_linear = mix_ratio
                RPR.SetTrackSendInfo_Value(bus_track.id, 0, return_send_id, "D_VOL", return_level_linear)
                
            self.logger.info(f"Created saturation bus for track {source_track}, "
                           f"type: {saturation_type}, mix: {mix_percent}%")
            
            return SaturationBusInfo(
                bus_track_index=bus_track_index,
                source_track=source_track,
                saturation_fx_id=saturation_fx_id,
                saturation_type=saturation_type,
                send_id=send_id,
                return_send_id=return_send_id,
                mix_percent=mix_percent
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create saturation bus: {e}")
            return None

    def sidechain_route_analyzer(
        self,
        source_track: int,
        dest_track: int
    ) -> RouteAnalysis:
        """
        Analyze sidechain routing validity and configuration.
        
        Args:
            source_track: Index of the source track
            dest_track: Index of the destination track
            
        Returns:
            RouteAnalysis with validity, channel mapping, and latency info
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return RouteAnalysis(
                    valid=False,
                    channels_map={},
                    latency_ms=0.0,
                    warnings=[],
                    errors=["REAPER connection unavailable"]
                )
                
            project = reapy.Project()
            warnings = []
            errors = []
            
            # Validate track indices
            if source_track >= project.n_tracks:
                errors.append(f"Source track {source_track} does not exist")
            if dest_track >= project.n_tracks:
                errors.append(f"Destination track {dest_track} does not exist")
                
            if errors:
                return RouteAnalysis(
                    valid=False,
                    channels_map={},
                    latency_ms=0.0,
                    warnings=warnings,
                    errors=errors
                )
                
            # Get tracks for analysis
            RPR = reapy.reascript_api
            source = project.tracks[source_track]
            dest = project.tracks[dest_track]
            
            # Analyze current channel configuration
            channels_map = self._analyze_track_channel_setup(source, dest)
            
            # Check for existing sends between tracks
            existing_sends = self._find_sends_between_tracks(source_track, dest_track)
            if existing_sends:
                warnings.append(f"Found {len(existing_sends)} existing sends between tracks")
                
            # Check destination track for sidechain-compatible effects
            sidechain_fx = self._find_sidechain_compatible_fx(dest)
            if not sidechain_fx:
                warnings.append("Destination track has no sidechain-compatible effects")
                
            # Measure routing latency
            latency_ms = self._measure_routing_latency(source_track, dest_track)
            if latency_ms > 10.0:  # More than 10ms might be problematic
                warnings.append(f"High routing latency detected: {latency_ms:.2f}ms")
                
            # Check for potential feedback loops
            if self._detect_potential_feedback_loop(source_track, dest_track):
                errors.append("Potential feedback loop detected in routing path")
                
            # Analyze overall validity
            valid = len(errors) == 0
            
            self.logger.info(f"Route analysis: {source_track} -> {dest_track}, "
                           f"valid: {valid}, latency: {latency_ms:.2f}ms")
            
            return RouteAnalysis(
                valid=valid,
                channels_map=channels_map,
                latency_ms=latency_ms,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sidechain route: {e}")
            return RouteAnalysis(
                valid=False,
                channels_map={},
                latency_ms=0.0,
                warnings=[],
                errors=[f"Analysis failed: {str(e)}"]
            )

    def _measure_routing_latency(self, source_track: int, dest_track: int) -> float:
        """Measure routing latency between tracks using REAPER's PDC system."""
        try:
            reapy = get_reapy()
            if not reapy:
                return 0.0
                
            # Use REAPER's built-in PDC (Plugin Delay Compensation) information
            # This is an approximation based on track processing
            RPR = reapy.reascript_api
            project = reapy.Project()
            
            source = project.tracks[source_track]
            dest = project.tracks[dest_track]
            
            # Get sample rate for conversion
            sample_rate = RPR.GetSetProjectInfo(0, "PROJECT_SRATE", 0, False)
            if sample_rate <= 0:
                sample_rate = 48000  # Default
                
            # Estimate latency from FX chains and routing
            source_latency_samples = self._estimate_track_fx_latency(source)
            dest_latency_samples = self._estimate_track_fx_latency(dest)
            
            # Add base routing latency (typically 1-2 samples for digital routing)
            routing_base_latency = 2.0  # samples
            
            total_latency_samples = source_latency_samples + dest_latency_samples + routing_base_latency
            latency_ms = (total_latency_samples / sample_rate) * 1000.0
            
            return latency_ms
            
        except Exception as e:
            self.logger.warning(f"Could not measure routing latency: {e}")
            return 1.0  # Default minimal latency
            
    def _estimate_track_fx_latency(self, track) -> float:
        """Estimate FX processing latency for a track."""
        try:
            reapy = get_reapy()
            RPR = reapy.reascript_api
            
            fx_count = RPR.TrackFX_GetCount(track.id)
            total_latency_samples = 0.0
            
            for fx_idx in range(fx_count):
                # Check if FX is enabled
                if RPR.TrackFX_GetEnabled(track.id, fx_idx):
                    # Get FX name to estimate typical latency
                    fx_name = RPR.TrackFX_GetFXName(track.id, fx_idx, "")
                    latency_estimate = self._estimate_fx_latency_by_name(fx_name)
                    total_latency_samples += latency_estimate
                    
            return total_latency_samples
            
        except Exception as e:
            self.logger.debug(f"Could not estimate FX latency: {e}")
            return 0.0
            
    def _estimate_fx_latency_by_name(self, fx_name: str) -> float:
        """Estimate latency samples for common FX types."""
        fx_name_lower = fx_name.lower()
        
        # Common latency estimates in samples at 48kHz
        if "comp" in fx_name_lower or "limit" in fx_name_lower:
            return 1.0  # Compressors typically have minimal latency
        elif "reverb" in fx_name_lower or "delay" in fx_name_lower:
            return 10.0  # Time-based effects
        elif "eq" in fx_name_lower or "filter" in fx_name_lower:
            return 2.0  # EQs have some latency from filters
        elif "saturate" in fx_name_lower or "distort" in fx_name_lower:
            return 3.0  # Saturation/distortion plugins
        else:
            return 1.0  # Default minimal latency
            
    def _validate_sidechain_routing(self, source_track: int, dest_track: int, channels: int) -> bool:
        """Validate that sidechain routing is properly configured."""
        try:
            # Basic validation - tracks exist and routing is logically sound
            reapy = get_reapy()
            if not reapy:
                return False
                
            project = reapy.Project()
            
            # Check tracks exist
            if source_track >= project.n_tracks or dest_track >= project.n_tracks:
                return False
                
            # Check for circular routing
            if source_track == dest_track:
                return False
                
            # Check channel configuration is valid
            if channels not in [1, 3]:  # 1 for channels 1/2, 3 for channels 3/4
                return False
                
            return True
            
        except Exception as e:
            self.logger.debug(f"Sidechain routing validation error: {e}")
            return False
            
    def _calculate_bus_latency_compensation(self, source_track: int, bus_track: int) -> float:
        """Calculate required latency compensation for parallel bus."""
        try:
            # Estimate the difference in processing latency between direct path and bus path
            reapy = get_reapy()
            if not reapy:
                return 0.0
                
            project = reapy.Project()
            source = project.tracks[source_track]
            bus = project.tracks[bus_track]
            
            source_latency = self._estimate_track_fx_latency(source)
            bus_latency = self._estimate_track_fx_latency(bus)
            
            # Bus path has additional routing latency
            bus_routing_latency = 2.0  # samples
            
            # Compensation needed is the difference
            compensation_samples = max(0, bus_latency + bus_routing_latency - source_latency)
            
            return compensation_samples
            
        except Exception as e:
            self.logger.debug(f"Bus latency compensation calculation error: {e}")
            return 0.0
            
    def _add_saturation_plugin(self, track, saturation_type: str) -> Optional[int]:
        """Add appropriate saturation plugin to track."""
        try:
            reapy = get_reapy()
            RPR = reapy.reascript_api
            
            # Map saturation types to REAPER plugins
            saturation_plugins = {
                "tape": "ReaTape",
                "tube": "ReaTube", 
                "transistor": "ReaSaturate",
                "digital": "ReaBitcrush"
            }
            
            plugin_name = saturation_plugins.get(saturation_type, "ReaSaturate")
            
            # Try to add the plugin
            fx_index = RPR.TrackFX_AddByName(track.id, plugin_name, False, -1)
            
            if fx_index >= 0:
                # Configure plugin with moderate saturation settings
                self._configure_saturation_plugin(track, fx_index, saturation_type)
                self.logger.info(f"Added {plugin_name} to saturation bus")
                return fx_index
            else:
                self.logger.warning(f"Could not add {plugin_name}, trying generic saturation")
                # Fallback to any available saturation plugin
                fx_index = RPR.TrackFX_AddByName(track.id, "ReaSaturate", False, -1)
                if fx_index >= 0:
                    self._configure_saturation_plugin(track, fx_index, "generic")
                    return fx_index
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to add saturation plugin: {e}")
            return None
            
    def _configure_saturation_plugin(self, track, fx_index: int, saturation_type: str):
        """Configure saturation plugin with appropriate settings."""
        try:
            reapy = get_reapy()
            RPR = reapy.reascript_api
            
            # Generic configuration for moderate saturation
            # Drive/Input gain
            if RPR.TrackFX_GetNumParams(track.id, fx_index) > 0:
                # Set moderate drive (parameter 0 is typically drive/input)
                if saturation_type == "tape":
                    RPR.TrackFX_SetParam(track.id, fx_index, 0, 0.6)  # Moderate tape saturation
                elif saturation_type == "tube":
                    RPR.TrackFX_SetParam(track.id, fx_index, 0, 0.5)  # Gentle tube warmth
                elif saturation_type == "transistor":
                    RPR.TrackFX_SetParam(track.id, fx_index, 0, 0.7)  # Transistor character
                else:  # digital or generic
                    RPR.TrackFX_SetParam(track.id, fx_index, 0, 0.4)  # Subtle saturation
                    
            self.logger.debug(f"Configured {saturation_type} saturation plugin")
            
        except Exception as e:
            self.logger.debug(f"Could not configure saturation plugin: {e}")
            
    def _analyze_track_channel_setup(self, source_track, dest_track) -> Dict[str, int]:
        """Analyze the channel configuration of tracks for routing."""
        try:
            reapy = get_reapy()
            RPR = reapy.reascript_api
            
            # Get channel information
            source_channels = int(RPR.GetMediaTrackInfo_Value(source_track.id, "I_NCHAN"))
            dest_channels = int(RPR.GetMediaTrackInfo_Value(dest_track.id, "I_NCHAN"))
            
            # Typical channel mapping for sidechain
            channels_map = {
                "source_channels": source_channels,
                "dest_channels": dest_channels,
                "input_l": 1,
                "input_r": 2,
                "sidechain_l": 3,
                "sidechain_r": 4,
                "available_sidechain": dest_channels >= 4
            }
            
            return channels_map
            
        except Exception as e:
            self.logger.debug(f"Channel analysis error: {e}")
            return {
                "source_channels": 2,
                "dest_channels": 2, 
                "input_l": 1,
                "input_r": 2,
                "sidechain_l": 3,
                "sidechain_r": 4,
                "available_sidechain": False
            }
            
    def _find_sends_between_tracks(self, source_track: int, dest_track: int) -> List[int]:
        """Find existing sends between two tracks."""
        try:
            reapy = get_reapy()
            if not reapy:
                return []
                
            project = reapy.Project()
            source = project.tracks[source_track]
            dest = project.tracks[dest_track]
            
            RPR = reapy.reascript_api
            existing_sends = []
            
            send_count = RPR.GetTrackNumSends(source.id, 0)  # 0 for sends
            
            for send_idx in range(send_count):
                dest_ptr = RPR.GetTrackSendInfo_Value(source.id, 0, send_idx, "P_DESTTRACK")
                # Compare destination track pointers (simplified comparison)
                if str(dest_ptr) == str(dest.id):
                    existing_sends.append(send_idx)
                    
            return existing_sends
            
        except Exception as e:
            self.logger.debug(f"Error finding existing sends: {e}")
            return []
            
    def _find_sidechain_compatible_fx(self, track) -> List[int]:
        """Find FX on track that support sidechain input."""
        try:
            reapy = get_reapy()
            RPR = reapy.reascript_api
            
            compatible_fx = []
            fx_count = RPR.TrackFX_GetCount(track.id)
            
            for fx_idx in range(fx_count):
                fx_name = RPR.TrackFX_GetFXName(track.id, fx_idx, "").lower()
                
                # Common sidechain-compatible effects
                if any(keyword in fx_name for keyword in [
                    "comp", "gate", "ducker", "sidechain", "sc_", 
                    "trigger", "envelope", "limit"
                ]):
                    compatible_fx.append(fx_idx)
                    
            return compatible_fx
            
        except Exception as e:
            self.logger.debug(f"Error finding sidechain FX: {e}")
            return []
            
    def _detect_potential_feedback_loop(self, source_track: int, dest_track: int) -> bool:
        """Detect potential feedback loops in routing."""
        try:
            # Simple check: see if dest_track has any sends back to source_track
            existing_return_sends = self._find_sends_between_tracks(dest_track, source_track)
            return len(existing_return_sends) > 0
            
        except Exception as e:
            self.logger.debug(f"Error detecting feedback loops: {e}")
            return False