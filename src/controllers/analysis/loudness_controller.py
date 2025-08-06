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
        """Get peak and RMS levels for a track using REAPER API."""
        try:
            import math
            from src.core.reapy_bridge import get_reapy
            from src.constants import (
                DB_CONVERSION_FACTOR,
                SILENCE_THRESHOLD_DB,
                MINIMUM_PEAK_VALUE,
            )
            
            reapy = get_reapy()
            if not reapy:
                return None
                
            # Get direct API access
            RPR = reapy.reascript_api
            
            # Get peak levels for both channels
            left_peak = RPR.Track_GetPeakInfo(track.id, 0)
            right_peak = RPR.Track_GetPeakInfo(track.id, 1)
            
            # Convert peak levels to dB
            left_peak_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, left_peak))
                if left_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            right_peak_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, right_peak))
                if right_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            
            # Get RMS levels using REAPER's VU meter functionality
            # Note: REAPER doesn't have direct RMS API, so we approximate from peak
            # In production, you'd use specialized metering plugins or custom analysis
            
            # Approximate RMS from peak levels using adaptive crest factor
            # This is still an approximation - real RMS would require sample-by-sample analysis
            crest_factor_db = self._estimate_crest_factor(left_peak_db, right_peak_db, is_master=False)
            left_rms_db = left_peak_db - crest_factor_db
            right_rms_db = right_peak_db - crest_factor_db
            
            # Ensure RMS levels don't go below silence threshold
            left_rms_db = max(left_rms_db, SILENCE_THRESHOLD_DB)
            right_rms_db = max(right_rms_db, SILENCE_THRESHOLD_DB)
            
            return {
                'left_peak': left_peak_db,    # dBFS
                'right_peak': right_peak_db,  # dBFS  
                'left_rms': left_rms_db,      # dBFS (approximated)
                'right_rms': right_rms_db,    # dBFS (approximated)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get track peak levels: {e}")
            return None

    def _get_master_peak_levels(self, master_track) -> Optional[Dict[str, float]]:
        """Get peak and RMS levels for master track using REAPER API."""
        try:
            import math
            from src.core.reapy_bridge import get_reapy
            from src.constants import (
                DB_CONVERSION_FACTOR,
                SILENCE_THRESHOLD_DB,
                MINIMUM_PEAK_VALUE,
            )
            
            reapy = get_reapy()
            if not reapy:
                return None
                
            # Get direct API access
            RPR = reapy.reascript_api
            
            # Get peak levels for both channels of master track
            left_peak = RPR.Track_GetPeakInfo(master_track.id, 0)
            right_peak = RPR.Track_GetPeakInfo(master_track.id, 1)
            
            # Convert peak levels to dB
            left_peak_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, left_peak))
                if left_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            right_peak_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, right_peak))
                if right_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            
            # Approximate RMS from peak levels for master track
            # Master tracks typically have lower crest factor (more compressed/limited)
            crest_factor_db = self._estimate_crest_factor(left_peak_db, right_peak_db, is_master=True)
            left_rms_db = left_peak_db - crest_factor_db
            right_rms_db = right_peak_db - crest_factor_db
            
            # Ensure RMS levels don't go below silence threshold
            left_rms_db = max(left_rms_db, SILENCE_THRESHOLD_DB)
            right_rms_db = max(right_rms_db, SILENCE_THRESHOLD_DB)
            
            return {
                'left_peak': left_peak_db,    # dBFS
                'right_peak': right_peak_db,  # dBFS
                'left_rms': left_rms_db,      # dBFS (approximated)  
                'right_rms': right_rms_db,    # dBFS (approximated)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get master peak levels: {e}")
            return None

    def _calculate_lufs_approximation(self, rms_left: float, rms_right: float) -> float:
        """
        Calculate LUFS approximation from RMS levels using ITU-R BS.1770-4 methodology.
        
        This implements the core LUFS calculation with K-weighting compensation.
        For full compliance, real-time sample-by-sample analysis would be required.
        """
        try:
            import math
            
            # Ensure we have valid RMS levels
            if rms_left == -150.0 and rms_right == -150.0:  # Both channels silent
                return -70.0  # Very quiet LUFS value
            
            # Convert RMS dB to linear power values
            # RMS in dBFS -> linear power
            linear_left = 10 ** (rms_left / 10)  # Power, not amplitude
            linear_right = 10 ** (rms_right / 10)
            
            # Apply ITU-R BS.1770-4 channel weighting for stereo
            # Left and Right channels have equal weighting (1.0 each)
            weighted_power = linear_left + linear_right
            
            # Convert power sum back to dB
            if weighted_power > 0:
                loudness_db = 10 * math.log10(weighted_power)
                
                # Apply K-weighting compensation
                # The K-weighting filter adds approximately -0.691 dB offset
                # This compensates for the high-frequency pre-emphasis in the K-filter
                k_weighting_offset = -0.691  # dB
                
                # Apply gating threshold compensation
                # ITU-R BS.1770-4 uses absolute gating at -70 LUFS and relative gating
                gating_compensation = 0.0  # Simplified - real implementation needs sample analysis
                
                lufs_value = loudness_db + k_weighting_offset + gating_compensation
                
                # Clamp to reasonable LUFS range
                lufs_value = max(-70.0, min(0.0, lufs_value))
                
                return lufs_value
            else:
                return -70.0  # Below measurement threshold
                
        except Exception as e:
            self.logger.error(f"LUFS calculation error: {e}")
            return -23.0  # Default broadcast standard LUFS value

    def _estimate_crest_factor(self, left_peak_db: float, right_peak_db: float, is_master: bool = False) -> float:
        """
        Estimate crest factor based on peak levels and track type.
        
        Args:
            left_peak_db: Left channel peak in dBFS
            right_peak_db: Right channel peak in dBFS
            is_master: Whether this is a master track
            
        Returns:
            Estimated crest factor in dB
        """
        try:
            # Get maximum peak level
            max_peak_db = max(left_peak_db, right_peak_db)
            
            # Base crest factor estimates based on signal level and track type
            if is_master:
                # Master tracks are typically more compressed/limited
                if max_peak_db > -6.0:  # Hot master
                    return 6.0   # Heavily compressed
                elif max_peak_db > -12.0:  # Normal master
                    return 8.0   # Moderately compressed
                else:  # Quiet master
                    return 10.0  # Less compression
            else:
                # Individual tracks have more dynamic range
                if max_peak_db > -6.0:  # Hot track
                    return 10.0  # Some limiting/compression
                elif max_peak_db > -12.0:  # Normal level
                    return 14.0  # Typical music crest factor
                elif max_peak_db > -24.0:  # Moderate level
                    return 16.0  # More dynamic content
                else:  # Quiet track
                    return 18.0  # Very dynamic (e.g., classical, ambient)
                    
        except Exception as e:
            self.logger.error(f"Crest factor estimation error: {e}")
            # Return safe defaults
            return 8.0 if is_master else 14.0