"""
Main analysis controller that orchestrates loudness and spectrum analysis.

Provides high-level interface for gain staging, automation generation,
and clip gain adjustment operations.
"""

import logging
import math
from typing import Optional, Dict, Any, List, Tuple

from src.core.reapy_bridge import get_reapy
from .loudness_controller import LoudnessController, LoudnessMetrics
from .spectrum_controller import SpectrumController, StereoImageMetrics, CrestFactorResult


class AnalysisController:
    """Main controller for audio analysis operations."""

    def __init__(self, debug: bool = False):
        """Initialize the analysis controller."""
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
            
        # Initialize sub-controllers
        self.loudness = LoudnessController(debug=debug)
        self.spectrum = SpectrumController(debug=debug)

    def write_volume_automation_to_target_lufs(
        self,
        track_index: int,
        target_lufs: float = -23.0,
        smoothing_ms: float = 100.0
    ) -> bool:
        """
        Generate volume automation to achieve target LUFS without clipping.
        
        Args:
            track_index: Index of track to automate
            target_lufs: Target LUFS level
            smoothing_ms: Automation smoothing time in milliseconds
            
        Returns:
            True if automation was created successfully
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return False
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                self.logger.error(f"Track index {track_index} out of range")
                return False
                
            track = project.tracks[track_index]
            
            # Measure current loudness
            current_metrics = self.loudness.loudness_measure_track(track_index)
            if not current_metrics:
                self.logger.error("Failed to measure track loudness")
                return False
                
            # Calculate required gain adjustment
            gain_adjustment = target_lufs - current_metrics.integrated_lufs
            
            # Check true peak limit to prevent clipping
            max_gain = -1.0 - current_metrics.true_peak_dbfs  # -1dBFS ceiling
            if gain_adjustment > max_gain:
                gain_adjustment = max_gain
                self.logger.warning(f"Gain limited to {gain_adjustment:.2f}dB to prevent clipping")
            
            # Create volume automation envelope
            try:
                volume_envelope = track.add_envelope("volume")
                if not volume_envelope:
                    self.logger.error("Failed to create volume envelope")
                    return False
                    
                # Convert gain adjustment to linear volume multiplier
                volume_multiplier = 10 ** (gain_adjustment / 20)
                current_volume = track.volume
                target_volume = current_volume * volume_multiplier
                
                # Add automation points with smoothing
                # Start point (current volume)
                volume_envelope.add_point(0.0, current_volume)
                
                # End point (target volume) with smoothing time
                smoothing_sec = smoothing_ms / 1000.0
                volume_envelope.add_point(smoothing_sec, target_volume)
                
                self.logger.info(f"Created volume automation: {gain_adjustment:+.2f}dB gain over {smoothing_ms}ms")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to create volume automation: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to write volume automation: {e}")
            return False

    def clip_gain_adjust(
        self,
        track_index: int,
        item_id: int,
        gain_db: float
    ) -> bool:
        """
        Adjust clip gain on an audio item without affecting track fader.
        
        Args:
            track_index: Index of track containing the item
            item_id: ID of the item to adjust
            gain_db: Gain adjustment in dB
            
        Returns:
            True if clip gain was adjusted successfully
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return False
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                return False
                
            track = project.tracks[track_index]
            
            # Find the item by ID
            target_item = None
            for item in track.items:
                # Use item position as a simple ID system
                if int(item.position * 1000) == item_id:  # Convert to ms for ID
                    target_item = item
                    break
                    
            if not target_item:
                self.logger.error(f"Item {item_id} not found on track {track_index}")
                return False
            
            # Adjust item volume (clip gain)
            try:
                # Get current item volume
                current_volume_db = 20 * math.log10(target_item.volume) if target_item.volume > 0 else -60.0
                new_volume_db = current_volume_db + gain_db
                new_volume_linear = 10 ** (new_volume_db / 20)
                
                # Apply new volume
                target_item.volume = new_volume_linear
                
                self.logger.info(f"Adjusted clip gain on item {item_id}: {gain_db:+.2f}dB")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to adjust item volume: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to adjust clip gain: {e}")
            return False

    def comprehensive_track_analysis(
        self,
        track_index: int,
        window_sec: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive analysis of a track including loudness,
        spectrum, stereo imaging, and dynamics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
            
        Returns:
            Dictionary containing all analysis results
        """
        try:
            analysis_results = {}
            
            # Loudness analysis
            loudness_metrics = self.loudness.loudness_measure_track(track_index, window_sec)
            if loudness_metrics:
                analysis_results['loudness'] = {
                    'integrated_lufs': loudness_metrics.integrated_lufs,
                    'short_term_lufs': loudness_metrics.short_term_lufs,
                    'momentary_lufs': loudness_metrics.momentary_lufs,
                    'lra': loudness_metrics.lra,
                    'true_peak_dbfs': loudness_metrics.true_peak_dbfs
                }
            
            # Spectrum analysis
            spectrum_data = self.spectrum.spectrum_analyzer_track(track_index, window_sec)
            if spectrum_data:
                # Extract key frequency bands
                analysis_results['spectrum'] = {
                    'low_freq_energy': self._get_frequency_band_energy(
                        spectrum_data.frequencies, spectrum_data.magnitudes_db, 20, 250
                    ),
                    'mid_freq_energy': self._get_frequency_band_energy(
                        spectrum_data.frequencies, spectrum_data.magnitudes_db, 250, 4000
                    ),
                    'high_freq_energy': self._get_frequency_band_energy(
                        spectrum_data.frequencies, spectrum_data.magnitudes_db, 4000, 20000
                    ),
                    'peak_frequency': self._find_peak_frequency(
                        spectrum_data.frequencies, spectrum_data.magnitudes_db
                    )
                }
            
            # Stereo imaging
            stereo_metrics = self.spectrum.stereo_image_metrics(track_index, window_sec)
            if stereo_metrics:
                analysis_results['stereo'] = {
                    'correlation': stereo_metrics.correlation,
                    'width': stereo_metrics.width,
                    'mid_level_db': stereo_metrics.mid_level_db,
                    'side_level_db': stereo_metrics.side_level_db,
                    'imbalance_db': stereo_metrics.imbalance_db
                }
            
            # Dynamics analysis
            crest_factor = self.spectrum.crest_factor_track(track_index, window_sec)
            if crest_factor:
                analysis_results['dynamics'] = {
                    'crest_factor_db': crest_factor.crest_factor_db,
                    'peak_db': crest_factor.peak_db,
                    'rms_db': crest_factor.rms_db,
                    'dynamic_range_db': crest_factor.dynamic_range_db
                }
            
            return analysis_results if analysis_results else None
            
        except Exception as e:
            self.logger.error(f"Failed to perform comprehensive analysis: {e}")
            return None

    def master_chain_analysis(
        self,
        window_sec: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze master chain for loudness standards compliance and quality.
        
        Args:
            window_sec: Analysis window in seconds
            
        Returns:
            Dictionary containing master analysis results and recommendations
        """
        try:
            master_analysis = {}
            
            # Master loudness analysis
            master_loudness = self.loudness.loudness_measure_master(window_sec)
            if master_loudness:
                master_analysis['loudness'] = {
                    'integrated_lufs': master_loudness.integrated_lufs,
                    'short_term_lufs': master_loudness.short_term_lufs,
                    'lra': master_loudness.lra,
                    'true_peak_dbfs': master_loudness.true_peak_dbfs,
                    'broadcast_compliant': self._check_broadcast_compliance(master_loudness),
                    'streaming_compliant': self._check_streaming_compliance(master_loudness)
                }
            
            # Master spectrum analysis
            master_spectrum = self.spectrum.spectrum_analyzer_master(window_sec)
            if master_spectrum:
                master_analysis['spectrum'] = {
                    'tonal_balance': self._analyze_tonal_balance(
                        master_spectrum.frequencies, master_spectrum.magnitudes_db
                    ),
                    'frequency_response': self._evaluate_frequency_response(
                        master_spectrum.frequencies, master_spectrum.magnitudes_db
                    )
                }
            
            # Master dynamics
            master_crest = self.spectrum.crest_factor_master(window_sec)
            if master_crest:
                master_analysis['dynamics'] = {
                    'crest_factor_db': master_crest.crest_factor_db,
                    'dynamic_range_quality': self._evaluate_dynamic_range(master_crest.crest_factor_db)
                }
            
            return master_analysis if master_analysis else None
            
        except Exception as e:
            self.logger.error(f"Failed to analyze master chain: {e}")
            return None

    def _get_frequency_band_energy(
        self, 
        frequencies: List[float], 
        magnitudes: List[float], 
        low_freq: float, 
        high_freq: float
    ) -> float:
        """Calculate average energy in a frequency band."""
        band_mags = []
        for i, freq in enumerate(frequencies):
            if low_freq <= freq <= high_freq:
                band_mags.append(magnitudes[i])
                
        if not band_mags:
            return -60.0
            
        # Calculate RMS average
        linear_sum = sum(10 ** (mag / 20) for mag in band_mags)
        rms_linear = math.sqrt(linear_sum / len(band_mags))
        return 20 * math.log10(rms_linear) if rms_linear > 0 else -60.0

    def _find_peak_frequency(
        self, 
        frequencies: List[float], 
        magnitudes: List[float]
    ) -> float:
        """Find frequency with highest magnitude."""
        if not magnitudes:
            return 1000.0
            
        peak_idx = magnitudes.index(max(magnitudes))
        return frequencies[peak_idx] if peak_idx < len(frequencies) else 1000.0

    def _check_broadcast_compliance(self, loudness: LoudnessMetrics) -> Dict[str, bool]:
        """Check compliance with broadcast standards."""
        return {
            'ebu_r128': -24.0 <= loudness.integrated_lufs <= -22.0,
            'atsc_a85': -25.0 <= loudness.integrated_lufs <= -23.0,
            'true_peak_ok': loudness.true_peak_dbfs <= -1.0,
            'lra_ok': loudness.lra <= 20.0
        }

    def _check_streaming_compliance(self, loudness: LoudnessMetrics) -> Dict[str, bool]:
        """Check compliance with streaming platform standards."""
        return {
            'spotify': -15.0 <= loudness.integrated_lufs <= -13.0,
            'apple_music': -17.0 <= loudness.integrated_lufs <= -15.0,
            'youtube': -15.0 <= loudness.integrated_lufs <= -13.0,
            'true_peak_streaming': loudness.true_peak_dbfs <= -1.0
        }

    def _analyze_tonal_balance(
        self, 
        frequencies: List[float], 
        magnitudes: List[float]
    ) -> Dict[str, str]:
        """Analyze overall tonal balance."""
        low_energy = self._get_frequency_band_energy(frequencies, magnitudes, 20, 250)
        mid_energy = self._get_frequency_band_energy(frequencies, magnitudes, 250, 4000)
        high_energy = self._get_frequency_band_energy(frequencies, magnitudes, 4000, 20000)
        
        # Simple balance evaluation
        balance = "balanced"
        if low_energy - mid_energy > 6:
            balance = "bass_heavy"
        elif mid_energy - low_energy > 6:
            balance = "mid_forward"
        elif high_energy - mid_energy > 6:
            balance = "bright"
        elif mid_energy - high_energy > 6:
            balance = "dull"
            
        return {
            'overall': balance,
            'low_energy_db': low_energy,
            'mid_energy_db': mid_energy,
            'high_energy_db': high_energy
        }

    def _evaluate_frequency_response(
        self, 
        frequencies: List[float], 
        magnitudes: List[float]
    ) -> str:
        """Evaluate overall frequency response quality."""
        # Calculate variance in magnitude response
        if len(magnitudes) < 10:
            return "insufficient_data"
            
        # Focus on 100Hz to 10kHz range
        relevant_mags = []
        for i, freq in enumerate(frequencies):
            if 100 <= freq <= 10000:
                relevant_mags.append(magnitudes[i])
                
        if not relevant_mags:
            return "no_midrange_data"
            
        # Calculate standard deviation
        mean_mag = sum(relevant_mags) / len(relevant_mags)
        variance = sum((mag - mean_mag) ** 2 for mag in relevant_mags) / len(relevant_mags)
        std_dev = math.sqrt(variance)
        
        if std_dev < 3:
            return "very_smooth"
        elif std_dev < 6:
            return "smooth"
        elif std_dev < 12:
            return "moderately_uneven"
        else:
            return "very_uneven"

    def _evaluate_dynamic_range(self, crest_factor_db: float) -> str:
        """Evaluate dynamic range quality."""
        if crest_factor_db < 6:
            return "highly_compressed"
        elif crest_factor_db < 12:
            return "compressed"
        elif crest_factor_db < 18:
            return "moderate_dynamics"
        elif crest_factor_db < 24:
            return "good_dynamics"
        else:
            return "excellent_dynamics"