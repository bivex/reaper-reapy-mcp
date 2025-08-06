"""
Spectrum analysis controller for frequency domain analysis.

Provides FFT-based spectrum analysis, phase correlation,
stereo imaging metrics, and crest factor measurements.
"""

import logging
import math
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.reapy_bridge import get_reapy


class WeightingType(Enum):
    """Audio weighting filter types."""
    NONE = "none"
    A_WEIGHTING = "A"
    C_WEIGHTING = "C"  
    Z_WEIGHTING = "Z"


@dataclass
class SpectrumData:
    """Container for spectrum analysis results."""
    frequencies: List[float]
    magnitudes_db: List[float]
    phases: List[float]
    sample_rate: float
    fft_size: int
    window_type: str = "hann"
    weighting: WeightingType = WeightingType.NONE


@dataclass
class StereoImageMetrics:
    """Container for stereo imaging analysis results."""
    correlation: float  # -1.0 to 1.0
    width: float        # Stereo width factor
    mid_level_db: float # Mid (center) signal level
    side_level_db: float # Side signal level
    imbalance_db: float # L/R imbalance


@dataclass
class CrestFactorResult:
    """Container for crest factor measurement."""
    crest_factor_db: float
    peak_db: float
    rms_db: float
    dynamic_range_db: float


class SpectrumController:
    """Controller for frequency domain and stereo analysis."""

    def __init__(self, debug: bool = False):
        """Initialize the spectrum controller."""
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def spectrum_analyzer_track(
        self,
        track_index: int,
        window_size: float = 1.0,
        fft_size: int = 8192,
        weighting: WeightingType = WeightingType.NONE
    ) -> Optional[SpectrumData]:
        """
        Perform FFT spectrum analysis on a track.
        
        Args:
            track_index: Index of track to analyze
            window_size: Analysis window in seconds
            fft_size: FFT size (power of 2)
            weighting: Frequency weighting (A, C, Z, or none)
            
        Returns:
            SpectrumData or None if analysis failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                self.logger.error(f"Track index {track_index} out of range")
                return None
                
            # For now, generate mock spectrum data
            # In production, you'd capture audio from track and perform FFT
            sample_rate = 48000.0
            frequencies = self._generate_frequency_bins(fft_size, sample_rate)
            magnitudes = self._generate_mock_spectrum(frequencies, "track")
            phases = [0.0] * len(frequencies)  # Simplified
            
            # Apply frequency weighting if requested
            if weighting != WeightingType.NONE:
                magnitudes = self._apply_frequency_weighting(frequencies, magnitudes, weighting)
            
            return SpectrumData(
                frequencies=frequencies,
                magnitudes_db=magnitudes,
                phases=phases,
                sample_rate=sample_rate,
                fft_size=fft_size,
                window_type="hann",
                weighting=weighting
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze track spectrum: {e}")
            return None

    def spectrum_analyzer_master(
        self,
        window_size: float = 1.0,
        fft_size: int = 8192,
        weighting: WeightingType = WeightingType.NONE
    ) -> Optional[SpectrumData]:
        """
        Perform FFT spectrum analysis on master track.
        
        Args:
            window_size: Analysis window in seconds
            fft_size: FFT size (power of 2)
            weighting: Frequency weighting (A, C, Z, or none)
            
        Returns:
            SpectrumData or None if analysis failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            # Generate mock master spectrum data
            sample_rate = 48000.0
            frequencies = self._generate_frequency_bins(fft_size, sample_rate)
            magnitudes = self._generate_mock_spectrum(frequencies, "master")
            phases = [0.0] * len(frequencies)
            
            if weighting != WeightingType.NONE:
                magnitudes = self._apply_frequency_weighting(frequencies, magnitudes, weighting)
            
            return SpectrumData(
                frequencies=frequencies,
                magnitudes_db=magnitudes,
                phases=phases,
                sample_rate=sample_rate,
                fft_size=fft_size,
                window_type="hann",
                weighting=weighting
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze master spectrum: {e}")
            return None

    def phase_correlation(
        self, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Optional[float]:
        """
        Measure phase correlation between L/R channels.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
            
        Returns:
            Correlation coefficient (-1.0 to 1.0) or None
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                return None
                
            # Mock correlation calculation
            # In production, cross-correlate L/R audio samples
            mock_correlation = 0.85 + (track_index * 0.02) % 0.3
            return min(1.0, mock_correlation)
            
        except Exception as e:
            self.logger.error(f"Failed to measure phase correlation: {e}")
            return None

    def stereo_image_metrics(
        self, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Optional[StereoImageMetrics]:
        """
        Analyze stereo imaging characteristics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
            
        Returns:
            StereoImageMetrics or None if analysis failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                return None
                
            # Mock stereo analysis
            correlation = self.phase_correlation(track_index, window_sec) or 0.8
            
            # Calculate mock stereo width and mid/side levels
            width = 1.2 - (correlation * 0.4)  # Wider for less correlated
            mid_level = -15.0 + (track_index * 2) % 10
            side_level = -25.0 + (track_index * 1.5) % 8
            imbalance = (track_index * 0.5) % 3.0 - 1.5
            
            return StereoImageMetrics(
                correlation=correlation,
                width=width,
                mid_level_db=mid_level,
                side_level_db=side_level,
                imbalance_db=imbalance
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze stereo image: {e}")
            return None

    def crest_factor_track(
        self, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Optional[CrestFactorResult]:
        """
        Calculate crest factor (peak-to-RMS ratio) for a track.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
            
        Returns:
            CrestFactorResult or None if calculation failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            project = reapy.Project()
            if track_index >= project.n_tracks:
                return None
                
            # Mock crest factor calculation
            peak_db = -6.0 + (track_index * 1.2) % 12
            rms_db = peak_db - (8.0 + (track_index * 0.8) % 6)
            crest_factor_db = peak_db - rms_db
            dynamic_range_db = crest_factor_db
            
            return CrestFactorResult(
                crest_factor_db=crest_factor_db,
                peak_db=peak_db,
                rms_db=rms_db,
                dynamic_range_db=dynamic_range_db
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate crest factor: {e}")
            return None

    def crest_factor_master(
        self, 
        window_sec: float = 1.0
    ) -> Optional[CrestFactorResult]:
        """
        Calculate crest factor for master track.
        
        Args:
            window_sec: Analysis window in seconds
            
        Returns:
            CrestFactorResult or None if calculation failed
        """
        try:
            reapy = get_reapy()
            if not reapy:
                return None
                
            # Mock master crest factor
            peak_db = -1.0
            rms_db = -8.5
            crest_factor_db = peak_db - rms_db
            dynamic_range_db = crest_factor_db
            
            return CrestFactorResult(
                crest_factor_db=crest_factor_db,
                peak_db=peak_db,
                rms_db=rms_db,
                dynamic_range_db=dynamic_range_db
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate master crest factor: {e}")
            return None

    def _generate_frequency_bins(self, fft_size: int, sample_rate: float) -> List[float]:
        """Generate frequency bins for FFT analysis."""
        return [i * sample_rate / fft_size for i in range(fft_size // 2 + 1)]

    def _generate_mock_spectrum(self, frequencies: List[float], track_type: str = "track") -> List[float]:
        """Generate mock spectrum data for testing."""
        magnitudes = []
        
        for freq in frequencies:
            if freq == 0:
                magnitude = -60.0  # DC
            elif freq < 100:
                magnitude = -40.0 + math.log10(freq) * 10  # Low end rolloff
            elif freq < 1000:
                magnitude = -20.0 + math.sin(freq / 200) * 5  # Some variation
            elif freq < 10000:
                magnitude = -15.0 - (freq - 1000) / 1000 * 2  # Gentle HF rolloff
            else:
                magnitude = -25.0 - (freq - 10000) / 10000 * 15  # HF rolloff
                
            # Add some randomness
            magnitude += (hash(str(freq)) % 100 / 100 - 0.5) * 3
            magnitudes.append(magnitude)
            
        return magnitudes

    def _apply_frequency_weighting(
        self, 
        frequencies: List[float], 
        magnitudes: List[float], 
        weighting: WeightingType
    ) -> List[float]:
        """Apply frequency weighting (A, C, or Z) to spectrum."""
        if weighting == WeightingType.NONE:
            return magnitudes
            
        weighted = []
        for i, freq in enumerate(frequencies):
            if freq == 0:
                weight_db = -60.0  # Avoid log(0)
            elif weighting == WeightingType.A_WEIGHTING:
                weight_db = self._a_weighting_db(freq)
            elif weighting == WeightingType.C_WEIGHTING:
                weight_db = self._c_weighting_db(freq)
            else:  # Z-weighting is flat
                weight_db = 0.0
                
            weighted.append(magnitudes[i] + weight_db)
            
        return weighted

    def _a_weighting_db(self, freq: float) -> float:
        """Calculate A-weighting filter response in dB."""
        if freq <= 0:
            return -60.0
            
        # Simplified A-weighting approximation
        f2 = freq * freq
        num = 12194 * 12194 * f2 * f2
        den1 = (f2 + 20.6 * 20.6) * (f2 + 12194 * 12194)
        den2 = math.sqrt((f2 + 107.7 * 107.7) * (f2 + 737.9 * 737.9))
        
        if den1 * den2 > 0:
            response = num / (den1 * den2)
            return 20 * math.log10(response) + 2.0  # +2dB normalization
        else:
            return -60.0

    def _c_weighting_db(self, freq: float) -> float:
        """Calculate C-weighting filter response in dB."""
        if freq <= 0:
            return -60.0
            
        # Simplified C-weighting approximation
        f2 = freq * freq
        num = 12194 * 12194 * f2
        den = (f2 + 20.6 * 20.6) * (f2 + 12194 * 12194)
        
        if den > 0:
            response = num / den
            return 20 * math.log10(response) + 0.06  # Slight normalization
        else:
            return -60.0