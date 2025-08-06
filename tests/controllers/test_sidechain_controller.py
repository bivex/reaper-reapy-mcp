"""
Tests for sidechain and bus routing controller.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import math

from src.controllers.routing.sidechain_controller import (
    SidechainController,
    SidechainInfo,
    ParallelBusInfo,
    SaturationBusInfo,
    RouteAnalysis,
    SidechainMode,
    SidechainChannels
)


@pytest.fixture
def mock_reapy():
    """Mock reapy for testing."""
    # Reset the reapy bridge cache before each test
    from src.core.reapy_bridge import reset_instances
    reset_instances()
    
    with patch('src.core.reapy_bridge.get_reapy') as mock:
        reapy_mock = Mock()
        project_mock = Mock()
        
        # Create track mocks with proper attributes  
        track1_mock = Mock(spec=['id', 'name'])
        track1_mock.id = 1001
        track1_mock.name = "Kick"
        
        track2_mock = Mock(spec=['id', 'name'])
        track2_mock.id = 1002
        track2_mock.name = "Bass"
        
        track3_mock = Mock(spec=['id', 'name'])
        track3_mock.id = 1003
        track3_mock.name = "Synth"
        
        master_mock = Mock(spec=['id'])
        master_mock.id = 1000
        
        # Mock the REAPER API
        rpr_mock = Mock()
        rpr_mock.CreateTrackSend.return_value = 0  # Successful send creation
        rpr_mock.SetTrackSendInfo_Value.return_value = True
        rpr_mock.InsertTrackAtIndex.return_value = True
        rpr_mock.GetSetMediaTrackInfo_String.return_value = True
        rpr_mock.SetMediaTrackInfo_Value.return_value = True
        rpr_mock.TrackFX_AddByName.return_value = 0  # Successful FX addition
        rpr_mock.TrackFX_SetParam.return_value = True
        rpr_mock.TrackFX_GetCount.return_value = 1
        rpr_mock.TrackFX_GetEnabled.return_value = True
        rpr_mock.TrackFX_GetFXName.return_value = "ReaComp"
        rpr_mock.TrackFX_GetNumParams.return_value = 4
        rpr_mock.GetTrackNumSends.return_value = 0
        rpr_mock.GetMediaTrackInfo_Value.return_value = 2  # 2 channels
        rpr_mock.GetSetProjectInfo.return_value = 48000  # Sample rate
        rpr_mock.UpdateArrange.return_value = True
        reapy_mock.reascript_api = rpr_mock
        reapy_mock.RPR = rpr_mock  # Some code uses RPR directly
        
        # Setup project structure
        project_mock.n_tracks = 3
        project_mock.tracks = [track1_mock, track2_mock, track3_mock]
        project_mock.master_track = master_mock
        
        reapy_mock.Project.return_value = project_mock
        mock.return_value = reapy_mock
        yield reapy_mock


class TestSidechainController:
    """Test sidechain and bus routing functionality."""
    
    def test_create_sidechain_send_basic(self, mock_reapy):
        """Test basic sidechain send creation."""
        controller = SidechainController(debug=True)
        
        result = controller.create_sidechain_send(
            source_track=0,
            destination_track=1,
            dest_channels=3,
            level_db=-6.0,
            pre_fader=True
        )
        
        assert result is not None
        assert isinstance(result, SidechainInfo)
        assert result.source_track == 0
        assert result.destination_track == 1
        assert result.sidechain_channels == 3
        assert result.level_db == -6.0
        assert result.pre_fader is True
        assert result.send_id >= 0
        
        # Verify REAPER API calls
        rpr = mock_reapy.reascript_api
        rpr.CreateTrackSend.assert_called_once()
        rpr.SetTrackSendInfo_Value.assert_called()

    def test_create_sidechain_send_channels_1_2(self, mock_reapy):
        """Test sidechain send to channels 1/2."""
        controller = SidechainController(debug=True)
        
        result = controller.create_sidechain_send(
            source_track=0,
            destination_track=1,
            dest_channels=1,  # Channels 1/2
            level_db=0.0,
            pre_fader=False
        )
        
        assert result is not None
        assert result.sidechain_channels == 1
        assert result.pre_fader is False

    def test_create_sidechain_send_invalid_track(self, mock_reapy):
        """Test sidechain send with invalid track index."""
        controller = SidechainController(debug=True)
        
        result = controller.create_sidechain_send(
            source_track=999,  # Invalid track
            destination_track=1
        )
        
        assert result is None

    def test_setup_parallel_bus_basic(self, mock_reapy):
        """Test basic parallel bus setup.""" 
        controller = SidechainController(debug=True)
        
        # Mock the project refresh for new track
        updated_project_mock = Mock()
        updated_project_mock.n_tracks = 4  # One more track after creation
        new_track_mock = Mock(spec=['id'])
        new_track_mock.id = 1004
        updated_project_mock.tracks = mock_reapy.Project().tracks + [new_track_mock]
        updated_project_mock.master_track = mock_reapy.Project().master_track
        
        # Make subsequent Project() calls return the updated project
        mock_reapy.Project.side_effect = [mock_reapy.Project(), updated_project_mock]
        
        result = controller.setup_parallel_bus(
            source_track=0,
            bus_name="Parallel Comp",
            mix_db=-3.0,
            latency_comp=True
        )
        
        assert result is not None
        assert isinstance(result, ParallelBusInfo)
        assert result.source_track == 0
        assert result.bus_name == "Parallel Comp"
        assert result.mix_db == -3.0
        assert result.latency_compensation is True
        assert result.bus_track_index >= 0
        
        # Verify track creation calls
        rpr = mock_reapy.reascript_api
        rpr.InsertTrackAtIndex.assert_called_once()
        rpr.GetSetMediaTrackInfo_String.assert_called()

    def test_add_saturation_bus_tape(self, mock_reapy):
        """Test saturation bus creation with tape saturation."""
        controller = SidechainController(debug=True)
        
        # Mock the project refresh for new track
        updated_project_mock = Mock()
        updated_project_mock.n_tracks = 4
        new_track_mock = Mock(spec=['id'])
        new_track_mock.id = 1004
        updated_project_mock.tracks = mock_reapy.Project().tracks + [new_track_mock]
        updated_project_mock.master_track = mock_reapy.Project().master_track
        
        mock_reapy.Project.side_effect = [mock_reapy.Project(), updated_project_mock]
        
        result = controller.add_saturation_bus(
            source_track=0,
            saturation_type="tape",
            mix_percent=25.0
        )
        
        assert result is not None
        assert isinstance(result, SaturationBusInfo)
        assert result.source_track == 0
        assert result.saturation_type == "tape"
        assert result.mix_percent == 25.0
        assert result.saturation_fx_id >= 0
        
        # Verify FX addition
        rpr = mock_reapy.reascript_api
        rpr.TrackFX_AddByName.assert_called()

    def test_add_saturation_bus_different_types(self, mock_reapy):
        """Test different saturation types."""
        controller = SidechainController(debug=True)
        
        saturation_types = ["tube", "transistor", "digital"]
        
        for sat_type in saturation_types:
            # Reset mocks for each iteration
            updated_project_mock = Mock()
            updated_project_mock.n_tracks = 4
            new_track_mock = Mock(spec=['id'])
            new_track_mock.id = 1004
            updated_project_mock.tracks = mock_reapy.Project().tracks + [new_track_mock]
            updated_project_mock.master_track = mock_reapy.Project().master_track
            
            mock_reapy.Project.side_effect = [mock_reapy.Project(), updated_project_mock]
            
            result = controller.add_saturation_bus(
                source_track=0,
                saturation_type=sat_type,
                mix_percent=30.0
            )
            
            assert result is not None
            assert result.saturation_type == sat_type

    def test_sidechain_route_analyzer_valid(self, mock_reapy):
        """Test sidechain route analysis for valid routing."""
        controller = SidechainController(debug=True)
        
        result = controller.sidechain_route_analyzer(
            source_track=0,
            dest_track=1
        )
        
        assert isinstance(result, RouteAnalysis)
        assert result.valid is True  # Should be valid for existing tracks
        assert isinstance(result.channels_map, dict)
        assert "source_channels" in result.channels_map
        assert "dest_channels" in result.channels_map
        assert result.latency_ms >= 0
        assert isinstance(result.warnings, list)
        assert isinstance(result.errors, list)

    def test_sidechain_route_analyzer_invalid_track(self, mock_reapy):
        """Test sidechain route analysis with invalid track."""
        controller = SidechainController(debug=True)
        
        result = controller.sidechain_route_analyzer(
            source_track=999,  # Invalid track
            dest_track=1
        )
        
        assert isinstance(result, RouteAnalysis)
        assert result.valid is False
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]

    def test_sidechain_route_analyzer_same_track(self, mock_reapy):
        """Test sidechain route analysis with same source and destination."""
        controller = SidechainController(debug=True)
        
        result = controller.sidechain_route_analyzer(
            source_track=0,
            dest_track=0  # Same track
        )
        
        # This should still analyze but may have warnings
        assert isinstance(result, RouteAnalysis)
        assert isinstance(result.channels_map, dict)

    def test_measure_routing_latency(self, mock_reapy):
        """Test routing latency measurement."""
        controller = SidechainController(debug=True)
        
        latency = controller._measure_routing_latency(0, 1)
        
        assert isinstance(latency, float)
        assert latency >= 0.0  # Latency should be non-negative

    def test_estimate_track_fx_latency(self, mock_reapy):
        """Test FX latency estimation."""
        controller = SidechainController(debug=True)
        
        track = mock_reapy.Project().tracks[0]
        latency = controller._estimate_track_fx_latency(track)
        
        assert isinstance(latency, float)
        assert latency >= 0.0

    def test_estimate_fx_latency_by_name(self, mock_reapy):
        """Test FX latency estimation by name."""
        controller = SidechainController(debug=True)
        
        # Test different FX types
        comp_latency = controller._estimate_fx_latency_by_name("ReaComp")
        reverb_latency = controller._estimate_fx_latency_by_name("ReaVerb")
        eq_latency = controller._estimate_fx_latency_by_name("ReaEQ")
        
        assert comp_latency > 0
        assert reverb_latency > comp_latency  # Reverb should have higher latency
        assert eq_latency > 0

    def test_validate_sidechain_routing_valid(self, mock_reapy):
        """Test sidechain routing validation for valid setup."""
        controller = SidechainController(debug=True)
        
        valid = controller._validate_sidechain_routing(0, 1, 3)
        assert valid is True

    def test_validate_sidechain_routing_invalid_channels(self, mock_reapy):
        """Test sidechain routing validation with invalid channels."""
        controller = SidechainController(debug=True)
        
        valid = controller._validate_sidechain_routing(0, 1, 5)  # Invalid channel config
        assert valid is False

    def test_validate_sidechain_routing_same_track(self, mock_reapy):
        """Test sidechain routing validation with same source/dest."""
        controller = SidechainController(debug=True)
        
        valid = controller._validate_sidechain_routing(0, 0, 3)  # Same track
        assert valid is False

    def test_add_saturation_plugin_success(self, mock_reapy):
        """Test successful saturation plugin addition."""
        controller = SidechainController(debug=True)
        
        track = mock_reapy.Project().tracks[0]
        fx_id = controller._add_saturation_plugin(track, "tape")
        
        assert fx_id is not None
        assert fx_id >= 0
        
        # Verify plugin was added
        rpr = mock_reapy.reascript_api
        rpr.TrackFX_AddByName.assert_called()

    def test_add_saturation_plugin_fallback(self, mock_reapy):
        """Test saturation plugin fallback when first choice fails."""
        controller = SidechainController(debug=True)
        
        # Mock first plugin addition to fail, second to succeed
        rpr = mock_reapy.reascript_api
        rpr.TrackFX_AddByName.side_effect = [-1, 0]  # First fails, second succeeds
        
        track = mock_reapy.Project().tracks[0]
        fx_id = controller._add_saturation_plugin(track, "nonexistent_type")
        
        assert fx_id is not None
        assert fx_id >= 0
        
        # Should have been called twice (first failed, then fallback)
        assert rpr.TrackFX_AddByName.call_count == 2

    def test_configure_saturation_plugin(self, mock_reapy):
        """Test saturation plugin configuration."""
        controller = SidechainController(debug=True)
        
        track = mock_reapy.Project().tracks[0]
        controller._configure_saturation_plugin(track, 0, "tape")
        
        # Verify parameter was set
        rpr = mock_reapy.reascript_api
        rpr.TrackFX_SetParam.assert_called()

    def test_analyze_track_channel_setup(self, mock_reapy):
        """Test track channel setup analysis."""
        controller = SidechainController(debug=True)
        
        source = mock_reapy.Project().tracks[0]
        dest = mock_reapy.Project().tracks[1]
        
        channels_map = controller._analyze_track_channel_setup(source, dest)
        
        assert isinstance(channels_map, dict)
        assert "source_channels" in channels_map
        assert "dest_channels" in channels_map
        assert "input_l" in channels_map
        assert "sidechain_l" in channels_map
        assert channels_map["input_l"] == 1
        assert channels_map["sidechain_l"] == 3

    def test_find_sidechain_compatible_fx(self, mock_reapy):
        """Test finding sidechain-compatible FX on track."""
        controller = SidechainController(debug=True)
        
        track = mock_reapy.Project().tracks[0]
        compatible_fx = controller._find_sidechain_compatible_fx(track)
        
        assert isinstance(compatible_fx, list)
        # With ReaComp mock, should find compatible FX
        assert len(compatible_fx) > 0

    def test_detect_potential_feedback_loop(self, mock_reapy):
        """Test feedback loop detection.""" 
        controller = SidechainController(debug=True)
        
        # Mock no return sends for clean test
        rpr = mock_reapy.reascript_api
        rpr.GetTrackNumSends.return_value = 0
        
        feedback = controller._detect_potential_feedback_loop(0, 1)
        
        assert isinstance(feedback, bool)
        # With no sends, should not detect feedback
        assert feedback is False

    def test_no_reapy_connection(self):
        """Test graceful handling when REAPER is not connected."""
        with patch('src.core.reapy_bridge.get_reapy', return_value=None):
            controller = SidechainController(debug=True)
            
            # Should return None when no REAPER connection
            sidechain_result = controller.create_sidechain_send(0, 1)
            assert sidechain_result is None
            
            bus_result = controller.setup_parallel_bus(0, "Test Bus")
            assert bus_result is None
            
            sat_result = controller.add_saturation_bus(0, "tape")
            assert sat_result is None
            
            # Route analyzer should return error state
            analysis_result = controller.sidechain_route_analyzer(0, 1)
            assert analysis_result.valid is False
            assert "REAPER connection unavailable" in analysis_result.errors

    def test_sidechain_send_creation_failure(self, mock_reapy):
        """Test handling of sidechain send creation failure."""
        controller = SidechainController(debug=True)
        
        # Mock CreateTrackSend to fail
        rpr = mock_reapy.reascript_api
        rpr.CreateTrackSend.return_value = -1  # Failure
        
        result = controller.create_sidechain_send(0, 1)
        
        assert result is None

    def test_parallel_bus_track_creation_success(self, mock_reapy):
        """Test successful parallel bus track creation and setup."""
        controller = SidechainController(debug=True)
        
        # Create comprehensive mock for project refresh
        original_project = mock_reapy.Project()
        
        # Updated project after track creation
        updated_project_mock = Mock()
        updated_project_mock.n_tracks = original_project.n_tracks + 1
        
        # Create new bus track mock
        bus_track_mock = Mock(spec=['id'])
        bus_track_mock.id = 1004
        
        # Add new track to track list
        updated_project_mock.tracks = list(original_project.tracks) + [bus_track_mock]
        updated_project_mock.master_track = original_project.master_track
        
        # Configure Project() to return updated project on second call
        mock_reapy.Project.side_effect = [original_project, updated_project_mock]
        
        result = controller.setup_parallel_bus(
            source_track=0,
            bus_name="Test Bus",
            mix_db=-6.0,
            latency_comp=True
        )
        
        assert result is not None
        assert result.bus_track_index == 3  # Should be the new track index
        assert result.bus_name == "Test Bus"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])