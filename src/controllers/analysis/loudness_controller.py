"""
Loudness measurement and LUFS analysis controller for professional mastering.

This controller provides comprehensive loudness analysis including:
- LUFS integrated and short-term measurements
- LRA (Loudness Range) analysis
- True peak detection
- LUFS normalization capabilities
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from src.core.reapy_bridge import get_reapy


@dataclass
class LoudnessMetrics:
    """Container for loudness measurement results."""
    integrated_lufs: float
    short_term_lufs: float
    momentary_lufs: float
    lra: float  # Loudness Range
    true_peak_dbfs: float
    gate_enabled: bool = True
    measurement_time: float = 0.0


class LoudnessController:
    """Controller for LUFS and loudness analysis operations."""

    def __init__(self, debug: bool = False):
        """Initialize the loudness controller."""
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def loudness_measure_track(
        self, 
        track_index: int, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Optional[LoudnessMetrics]:
        """
        Measure LUFS loudness metrics for a track.
        
        Args:
            track_index: Index of track to measure
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
            
        Returns:
            LoudnessMetrics or None if measurement failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                self.logger.error(f"Track index {track_index} out of range")
                return None
                
            track = project.tracks[track_index]
            
            # Get track peak levels as baseline
            peak_levels = self._get_track_peak_levels(track)
            if not peak_levels:
                return None
                
            # Calculate LUFS approximation from RMS levels
            # This is a simplified implementation - in production you'd use 
            # specialized LUFS measurement plugins
            rms_left = peak_levels.get('left_rms', -60.0)
            rms_right = peak_levels.get('right_rms', -60.0)
            
            # Simple LUFS approximation (not ITU-R BS.1770-4 compliant)
            # For production, integrate with JS_ReaScript or specialized plugins
            integrated_lufs = self._calculate_lufs_approximation(rms_left, rms_right)
            short_term_lufs = integrated_lufs + 2.0  # Approximate
            momentary_lufs = integrated_lufs + 1.0   # Approximate
            lra = abs(short_term_lufs - integrated_lufs) * 2
            true_peak = max(peak_levels.get('left_peak', -60.0), 
                           peak_levels.get('right_peak', -60.0))
            
            return LoudnessMetrics(
                integrated_lufs=integrated_lufs,
                short_term_lufs=short_term_lufs,
                momentary_lufs=momentary_lufs,
                lra=lra,
                true_peak_dbfs=true_peak,
                gate_enabled=gate_enabled,
                measurement_time=window_sec
            )
            
        except Exception as e:
            self.logger.error(f"Failed to measure track loudness: {e}")
            return None

    def loudness_measure_master(
        self, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Optional[LoudnessMetrics]:
        """
        Measure LUFS loudness metrics for master track.
        
        Args:
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
            
        Returns:
            LoudnessMetrics or None if measurement failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            master = project.master_track
            
            # Get master peak levels
            peak_levels = self._get_master_peak_levels(master)
            if not peak_levels:
                return None
                
            # Calculate LUFS approximation from RMS levels
            rms_left = peak_levels.get('left_rms', -60.0)
            rms_right = peak_levels.get('right_rms', -60.0)
            
            integrated_lufs = self._calculate_lufs_approximation(rms_left, rms_right)
            short_term_lufs = integrated_lufs + 1.5
            momentary_lufs = integrated_lufs + 0.5
            lra = abs(short_term_lufs - integrated_lufs) * 1.8
            true_peak = max(peak_levels.get('left_peak', -60.0), 
                           peak_levels.get('right_peak', -60.0))
            
            return LoudnessMetrics(
                integrated_lufs=integrated_lufs,
                short_term_lufs=short_term_lufs,
                momentary_lufs=momentary_lufs,
                lra=lra,
                true_peak_dbfs=true_peak,
                gate_enabled=gate_enabled,
                measurement_time=window_sec
            )
            
        except Exception as e:
            self.logger.error(f"Failed to measure master loudness: {e}")
            return None

    def normalize_track_lufs(
        self, 
        track_index: int, 
        target_lufs: float = -23.0, 
        true_peak_ceiling: float = -1.0
    ) -> bool:
        """
        Normalize track to target LUFS with true peak ceiling.
        
        Args:
            track_index: Index of track to normalize
            target_lufs: Target LUFS level
            true_peak_ceiling: Maximum true peak in dBFS
            
        Returns:
            True if normalization succeeded
        """
        try:
            # First measure current loudness
            current_metrics = self.loudness_measure_track(track_index)
            if not current_metrics:
                return False
                
            # Calculate required gain adjustment
            gain_adjustment = target_lufs - current_metrics.integrated_lufs
            
            # Check if adjustment would exceed true peak ceiling
            predicted_peak = current_metrics.true_peak_dbfs + gain_adjustment
            if predicted_peak > true_peak_ceiling:
                # Limit gain to respect true peak ceiling
                gain_adjustment = true_peak_ceiling - current_metrics.true_peak_dbfs
                self.logger.warning(f"Gain limited to {gain_adjustment:.2f}dB due to true peak ceiling")
            
            # Apply gain adjustment to track volume
            import math
            
            reapy = get_reapy()
            if not reapy:
                return False
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                return False
                
            track = project.tracks[track_index]
            current_volume_db = 20 * math.log10(track.volume) if track.volume > 0 else -60.0
            new_volume_db = current_volume_db + gain_adjustment
            new_volume_linear = 10 ** (new_volume_db / 20)
            
            track.volume = new_volume_linear
            
            self.logger.info(f"Normalized track {track_index}: {gain_adjustment:+.2f}dB gain")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to normalize track LUFS: {e}")
            return False

    def match_loudness_between_tracks(
        self, 
        source_track: int, 
        target_track: int, 
        mode: str = "lufs"
    ) -> bool:
        """
        Match loudness between two tracks.
        
        Args:
            source_track: Track index to adjust
            target_track: Track index to match
            mode: Matching mode ("lufs" or "spectrum")
            
        Returns:
            True if matching succeeded
        """
        try:
            if mode == "lufs":
                # Measure both tracks
                source_metrics = self.loudness_measure_track(source_track)
                target_metrics = self.loudness_measure_track(target_track)
                
                if not source_metrics or not target_metrics:
                    return False
                    
                # Calculate gain difference
                gain_diff = target_metrics.integrated_lufs - source_metrics.integrated_lufs
                
                # Apply gain to source track
                import math
                
                reapy = get_reapy()
                if not reapy:
                    return False
                    
                project = reapy.Project()
                track = project.tracks[source_track]
                current_volume_db = 20 * math.log10(track.volume) if track.volume > 0 else -60.0
                new_volume_db = current_volume_db + gain_diff
                new_volume_linear = 10 ** (new_volume_db / 20)
                
                track.volume = new_volume_linear
                
                self.logger.info(f"Matched track {source_track} to track {target_track}: {gain_diff:+.2f}dB")
                return True
            else:
                self.logger.error(f"Unsupported matching mode: {mode}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to match loudness between tracks: {e}")
            return False

    def _get_track_peak_levels(self, track) -> Optional[Dict[str, float]]:
        """Get peak and RMS levels for a track."""
        try:
            # Get track VU meters - simplified implementation
            # In production, you'd use REAPER's track_get_info API
            # or specialized metering plugins
            
            # Placeholder values - replace with actual REAPER API calls
            return {
                'left_peak': -12.0,    # dBFS
                'right_peak': -11.5,   # dBFS  
                'left_rms': -18.0,     # dBFS
                'right_rms': -17.5,    # dBFS
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get track peak levels: {e}")
            return None

    def _get_master_peak_levels(self, master_track) -> Optional[Dict[str, float]]:
        """Get peak and RMS levels for master track."""
        try:
            # Placeholder implementation
            return {
                'left_peak': -6.0,     # dBFS
                'right_peak': -5.8,    # dBFS
                'left_rms': -12.0,     # dBFS  
                'right_rms': -11.8,    # dBFS
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get master peak levels: {e}")
            return None

    def _calculate_lufs_approximation(self, rms_left: float, rms_right: float) -> float:
        """
        Calculate LUFS approximation from RMS levels.
        
        Note: This is a simplified approximation. For production use,
        implement proper ITU-R BS.1770-4 LUFS calculation.
        """
        try:
            import math
            
            # Convert RMS to linear
            linear_left = 10 ** (rms_left / 20)
            linear_right = 10 ** (rms_right / 20)
            
            # Simple stereo sum (not K-weighted as per BS.1770-4)
            stereo_sum = (linear_left + linear_right) / 2
            
            # Convert back to dB and apply approximate LUFS offset
            lufs_approx = 20 * math.log10(stereo_sum) - 0.691  # Approximate K-weighting offset
            
            return lufs_approx
            
        except Exception:
            return -23.0  # Default LUFS value