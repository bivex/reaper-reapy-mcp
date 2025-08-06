"""
Tests for analysis controllers including loudness and spectrum analysis.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import math

from src.controllers.analysis.analysis_controller import AnalysisController
from src.controllers.analysis.loudness_controller import LoudnessController, LoudnessMetrics
from src.controllers.analysis.spectrum_controller import (
    SpectrumController, 
    SpectrumData, 
    StereoImageMetrics, 
    CrestFactorResult,
    WeightingType
)


@pytest.fixture
def mock_reapy():
    """Mock reapy for testing."""
    with patch('src.core.reapy_bridge.get_reapy') as mock:
        reapy_mock = Mock()
        project_mock = Mock()
        
        # Create track mocks with proper attributes  
        track1_mock = Mock(spec=['volume', 'items', 'add_envelope'])
        track1_mock.volume = 1.0
        track1_mock.items = []
        track1_mock.add_envelope = Mock()
        
        track2_mock = Mock(spec=['volume', 'items', 'add_envelope'])
        track2_mock.volume = 1.0
        track2_mock.items = []
        track2_mock.add_envelope = Mock()
        
        track3_mock = Mock(spec=['volume', 'items', 'add_envelope'])
        track3_mock.volume = 1.0
        track3_mock.items = []
        track3_mock.add_envelope = Mock()
        
        master_mock = Mock()
        
        # Setup project structure
        project_mock.n_tracks = 3
        project_mock.tracks = [track1_mock, track2_mock, track3_mock]
        project_mock.master_track = master_mock
        
        reapy_mock.Project.return_value = project_mock
        mock.return_value = reapy_mock
        yield reapy_mock


class TestLoudnessController:
    """Test loudness measurement and LUFS analysis."""
    
    def test_loudness_measure_track(self, mock_reapy):
        """Test track loudness measurement."""
        controller = LoudnessController(debug=True)
        
        result = controller.loudness_measure_track(track_index=0, window_sec=10.0)
        
        assert result is not None
        assert isinstance(result, LoudnessMetrics)
        assert -60 < result.integrated_lufs < 0  # Reasonable LUFS range
        assert result.lra >= 0  # LRA should be positive
        assert -20 < result.true_peak_dbfs < 0  # Reasonable peak range
        assert result.measurement_time == 10.0

    def test_loudness_measure_master(self, mock_reapy):
        """Test master track loudness measurement."""
        controller = LoudnessController(debug=True)
        
        result = controller.loudness_measure_master(window_sec=20.0)
        
        assert result is not None
        assert isinstance(result, LoudnessMetrics)
        assert result.measurement_time == 20.0

    def test_normalize_track_lufs(self, mock_reapy):
        """Test LUFS normalization."""
        controller = LoudnessController(debug=True)
        
        # Use existing track mock and modify volume
        track_mock = mock_reapy.Project().tracks[0]
        track_mock.volume = 0.5  # -6dB
        
        result = controller.normalize_track_lufs(
            track_index=0, 
            target_lufs=-16.0, 
            true_peak_ceiling=-1.0
        )
        
        assert result is True
        # Volume should have been adjusted
        assert track_mock.volume != 0.5

    def test_match_loudness_between_tracks(self, mock_reapy):
        """Test loudness matching between tracks."""
        controller = LoudnessController(debug=True)
        
        result = controller.match_loudness_between_tracks(
            source_track=0,
            target_track=1,
            mode="lufs"
        )
        
        assert result is True

    def test_invalid_track_index(self, mock_reapy):
        """Test handling of invalid track indices."""
        controller = LoudnessController(debug=True)
        
        result = controller.loudness_measure_track(track_index=99)
        
        assert result is None


class TestSpectrumController:
    """Test spectrum analysis and stereo imaging."""
    
    def test_spectrum_analyzer_track(self, mock_reapy):
        """Test FFT spectrum analysis on track."""
        controller = SpectrumController(debug=True)
        
        result = controller.spectrum_analyzer_track(
            track_index=0,
            window_size=2.0,
            fft_size=4096,
            weighting=WeightingType.A_WEIGHTING
        )
        
        assert result is not None
        assert isinstance(result, SpectrumData)
        assert len(result.frequencies) == len(result.magnitudes_db)
        assert result.fft_size == 4096
        assert result.weighting == WeightingType.A_WEIGHTING
        assert result.sample_rate > 0

    def test_spectrum_analyzer_master(self, mock_reapy):
        """Test master spectrum analysis."""
        controller = SpectrumController(debug=True)
        
        result = controller.spectrum_analyzer_master(fft_size=2048)
        
        assert result is not None
        assert result.fft_size == 2048

    def test_phase_correlation(self, mock_reapy):
        """Test phase correlation measurement."""
        controller = SpectrumController(debug=True)
        
        result = controller.phase_correlation(track_index=0)
        
        assert result is not None
        assert -1.0 <= result <= 1.0  # Correlation must be in valid range

    def test_stereo_image_metrics(self, mock_reapy):
        """Test stereo imaging analysis."""
        controller = SpectrumController(debug=True)
        
        result = controller.stereo_image_metrics(track_index=0)
        
        assert result is not None
        assert isinstance(result, StereoImageMetrics)
        assert -1.0 <= result.correlation <= 1.0
        assert result.width > 0
        assert result.mid_level_db < 0  # dB values should be negative
        assert result.side_level_db < 0

    def test_crest_factor_track(self, mock_reapy):
        """Test crest factor calculation."""
        controller = SpectrumController(debug=True)
        
        result = controller.crest_factor_track(track_index=0)
        
        assert result is not None
        assert isinstance(result, CrestFactorResult)
        assert result.crest_factor_db > 0  # Peak should be higher than RMS
        assert result.peak_db > result.rms_db

    def test_crest_factor_master(self, mock_reapy):
        """Test master crest factor."""
        controller = SpectrumController(debug=True)
        
        result = controller.crest_factor_master()
        
        assert result is not None
        assert result.crest_factor_db > 0

    def test_frequency_weighting(self):
        """Test frequency weighting calculations."""
        controller = SpectrumController(debug=True)
        
        # Test A-weighting at 1kHz (should be close to 0dB)
        a_weight_1k = controller._a_weighting_db(1000.0)
        assert -3.0 < a_weight_1k < 3.0
        
        # Test C-weighting
        c_weight_1k = controller._c_weighting_db(1000.0)
        assert -2.0 < c_weight_1k < 2.0


class TestAnalysisController:
    """Test main analysis controller integration."""
    
    def test_write_volume_automation_to_target_lufs(self, mock_reapy):
        """Test volume automation generation."""
        controller = AnalysisController(debug=True)
        
        # Use existing track mock
        track_mock = mock_reapy.Project().tracks[0]
        envelope_mock = Mock()
        track_mock.add_envelope.return_value = envelope_mock
        
        result = controller.write_volume_automation_to_target_lufs(
            track_index=0,
            target_lufs=-18.0,
            smoothing_ms=250.0
        )
        
        assert result is True
        track_mock.add_envelope.assert_called_with("volume")
        envelope_mock.add_point.assert_called()

    def test_clip_gain_adjust(self, mock_reapy):
        """Test clip gain adjustment."""
        controller = AnalysisController(debug=True)
        
        # Use existing track mock and add item
        track_mock = mock_reapy.Project().tracks[0]
        item_mock = Mock(spec=['position', 'volume'])
        item_mock.position = 5.0  # 5 seconds
        item_mock.volume = 1.0
        track_mock.items = [item_mock]
        
        result = controller.clip_gain_adjust(
            track_index=0,
            item_id=5000,  # 5 seconds * 1000 = 5000ms ID
            gain_db=3.0
        )
        
        assert result is True
        # Volume should have been adjusted upward
        assert item_mock.volume > 1.0

    def test_comprehensive_track_analysis(self, mock_reapy):
        """Test comprehensive analysis integration."""
        controller = AnalysisController(debug=True)
        
        result = controller.comprehensive_track_analysis(track_index=0, window_sec=3.0)
        
        assert result is not None
        assert 'loudness' in result
        assert 'spectrum' in result
        assert 'stereo' in result
        assert 'dynamics' in result
        
        # Check loudness data
        loudness = result['loudness']
        assert 'integrated_lufs' in loudness
        assert 'lra' in loudness
        assert 'true_peak_dbfs' in loudness
        
        # Check spectrum data
        spectrum = result['spectrum']
        assert 'low_freq_energy' in spectrum
        assert 'mid_freq_energy' in spectrum
        assert 'high_freq_energy' in spectrum
        assert 'peak_frequency' in spectrum
        
        # Check stereo data
        stereo = result['stereo']
        assert 'correlation' in stereo
        assert 'width' in stereo
        
        # Check dynamics data
        dynamics = result['dynamics']
        assert 'crest_factor_db' in dynamics

    def test_master_chain_analysis(self, mock_reapy):
        """Test master chain analysis and compliance checking."""
        controller = AnalysisController(debug=True)
        
        result = controller.master_chain_analysis(window_sec=15.0)
        
        assert result is not None
        assert 'loudness' in result
        assert 'spectrum' in result
        assert 'dynamics' in result
        
        # Check broadcast compliance
        loudness = result['loudness']
        assert 'broadcast_compliant' in loudness
        assert 'streaming_compliant' in loudness
        
        compliance = loudness['broadcast_compliant']
        assert 'ebu_r128' in compliance
        assert 'true_peak_ok' in compliance
        
        streaming = loudness['streaming_compliant']
        assert 'spotify' in streaming
        assert 'apple_music' in streaming

    def test_frequency_band_energy_calculation(self):
        """Test frequency band energy calculation."""
        controller = AnalysisController(debug=True)
        
        # Test data
        frequencies = [100, 500, 1000, 5000, 10000]
        magnitudes = [-20, -15, -10, -18, -25]  # dB
        
        # Test mid-frequency band (250-4000 Hz)
        energy = controller._get_frequency_band_energy(
            frequencies, magnitudes, 250, 4000
        )
        
        # Should include 500, 1000 Hz points
        assert energy is not None
        assert -20 < energy < 0  # Should be reasonable dB value

    def test_tonal_balance_analysis(self):
        """Test tonal balance evaluation."""
        controller = AnalysisController(debug=True)
        
        frequencies = list(range(20, 20001, 100))  # 20Hz to 20kHz
        magnitudes = [-15] * len(frequencies)  # Flat response
        
        balance = controller._analyze_tonal_balance(frequencies, magnitudes)
        
        assert 'overall' in balance
        assert 'low_energy_db' in balance
        assert 'mid_energy_db' in balance
        assert 'high_energy_db' in balance
        assert balance['overall'] == 'balanced'

    def test_dynamic_range_evaluation(self):
        """Test dynamic range quality evaluation."""
        controller = AnalysisController(debug=True)
        
        # Test different crest factor ranges
        assert controller._evaluate_dynamic_range(4.0) == "highly_compressed"
        assert controller._evaluate_dynamic_range(8.0) == "compressed"
        assert controller._evaluate_dynamic_range(15.0) == "moderate_dynamics"
        assert controller._evaluate_dynamic_range(20.0) == "good_dynamics"
        assert controller._evaluate_dynamic_range(28.0) == "excellent_dynamics"

    def test_no_reapy_connection(self):
        """Test graceful handling when REAPER is not connected."""
        with patch('src.core.reapy_bridge.get_reapy', return_value=None):
            controller = AnalysisController(debug=True)
            
            # Should return None when no REAPER connection for certain functions
            automation_result = controller.write_volume_automation_to_target_lufs(
                track_index=0, target_lufs=-16.0
            )
            assert automation_result is False
            
            clip_result = controller.clip_gain_adjust(track_index=0, item_id=1000, gain_db=3.0)
            assert clip_result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])