"""MCP tools for audio analysis and metering."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
from ._helpers import _create_success_response, _create_error_response, _handle_controller_operation, logger

def _setup_analysis_tools(mcp: FastMCP, controller) -> None:
    """Setup audio analysis MCP tools for professional mixing and mastering."""

    @mcp.tool("loudness_measure_track")
    def loudness_measure_track(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Measure LUFS loudness metrics for a track.
        
        Args:
            track_index: Index of track to measure
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
        """
        try:
            metrics = controller.analysis.loudness.loudness_measure_track(
                track_index, window_sec, gate_enabled
            )
            if metrics:
                return _create_success_response(
                    f"Track {track_index} loudness: {metrics.integrated_lufs:.1f} LUFS, "
                    f"LRA: {metrics.lra:.1f} LU, True Peak: {metrics.true_peak_dbfs:.1f} dBFS"
                )
            else:
                return _create_error_response("Failed to measure track loudness")
        except Exception as e:
            logger.error(f"Failed to measure track loudness: {e}")
            return _create_error_response(f"Failed to measure track loudness: {str(e)}")

    @mcp.tool("loudness_measure_master")
    def loudness_measure_master(
        ctx: Context, 
        window_sec: float = 30.0, 
        gate_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Measure LUFS loudness metrics for master track.
        
        Args:
            window_sec: Measurement window in seconds
            gate_enabled: Enable gating per ITU-R BS.1770-4
        """
        try:
            metrics = controller.analysis.loudness.loudness_measure_master(
                window_sec, gate_enabled
            )
            if metrics:
                return _create_success_response(
                    f"Master loudness: {metrics.integrated_lufs:.1f} LUFS, "
                    f"LRA: {metrics.lra:.1f} LU, True Peak: {metrics.true_peak_dbfs:.1f} dBFS"
                )
            else:
                return _create_error_response("Failed to measure master loudness")
        except Exception as e:
            logger.error(f"Failed to measure master loudness: {e}")
            return _create_error_response(f"Failed to measure master loudness: {str(e)}")

    @mcp.tool("spectrum_analyzer_track")
    def spectrum_analyzer_track(
        ctx: Context,
        track_index: int,
        window_size: float = 1.0,
        fft_size: int = 8192,
        weighting: str = "none"
    ) -> Dict[str, Any]:
        """
        Perform FFT spectrum analysis on a track.
        
        Args:
            track_index: Index of track to analyze
            window_size: Analysis window in seconds
            fft_size: FFT size (power of 2)
            weighting: Frequency weighting (A, C, Z, or none)
        """
        try:
            from controllers.analysis.spectrum_controller import WeightingType
            
            weight_map = {
                "none": WeightingType.NONE,
                "A": WeightingType.A_WEIGHTING,
                "C": WeightingType.C_WEIGHTING,
                "Z": WeightingType.Z_WEIGHTING
            }
            weighting_type = weight_map.get(weighting, WeightingType.NONE)
            
            spectrum = controller.analysis.spectrum.spectrum_analyzer_track(
                track_index, window_size, fft_size, weighting_type
            )
            if spectrum:
                return _create_success_response(
                    f"Track {track_index} spectrum analyzed: {len(spectrum.frequencies)} frequency bins, "
                    f"SR: {spectrum.sample_rate}Hz, Weighting: {weighting}"
                )
            else:
                return _create_error_response("Failed to analyze track spectrum")
        except Exception as e:
            logger.error(f"Failed to analyze track spectrum: {e}")
            return _create_error_response(f"Failed to analyze track spectrum: {str(e)}")

    @mcp.tool("phase_correlation")
    def phase_correlation(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Measure phase correlation between L/R channels.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            correlation = controller.analysis.spectrum.phase_correlation(track_index, window_sec)
            if correlation is not None:
                return _create_success_response(
                    f"Track {track_index} phase correlation: {correlation:.3f}"
                )
            else:
                return _create_error_response("Failed to measure phase correlation")
        except Exception as e:
            logger.error(f"Failed to measure phase correlation: {e}")
            return _create_error_response(f"Failed to measure phase correlation: {str(e)}")

    @mcp.tool("stereo_image_metrics")
    def stereo_image_metrics(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Analyze stereo imaging characteristics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            metrics = controller.analysis.spectrum.stereo_image_metrics(track_index, window_sec)
            if metrics:
                return _create_success_response(
                    f"Track {track_index} stereo: Correlation: {metrics.correlation:.3f}, "
                    f"Width: {metrics.width:.2f}, Mid: {metrics.mid_level_db:.1f}dB, "
                    f"Side: {metrics.side_level_db:.1f}dB"
                )
            else:
                return _create_error_response("Failed to analyze stereo image")
        except Exception as e:
            logger.error(f"Failed to analyze stereo image: {e}")
            return _create_error_response(f"Failed to analyze stereo image: {str(e)}")

    @mcp.tool("crest_factor_track")
    def crest_factor_track(
        ctx: Context, 
        track_index: int, 
        window_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate crest factor (peak-to-RMS ratio) for a track.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            crest = controller.analysis.spectrum.crest_factor_track(track_index, window_sec)
            if crest:
                return _create_success_response(
                    f"Track {track_index} crest factor: {crest.crest_factor_db:.1f}dB "
                    f"(Peak: {crest.peak_db:.1f}dB, RMS: {crest.rms_db:.1f}dB)"
                )
            else:
                return _create_error_response("Failed to calculate crest factor")
        except Exception as e:
            logger.error(f"Failed to calculate crest factor: {e}")
            return _create_error_response(f"Failed to calculate crest factor: {str(e)}")

    @mcp.tool("normalize_track_lufs")
    def normalize_track_lufs(
        ctx: Context,
        track_index: int,
        target_lufs: float = -23.0,
        true_peak_ceiling: float = -1.0
    ) -> Dict[str, Any]:
        """
        Normalize track to target LUFS with true peak ceiling.
        
        Args:
            track_index: Index of track to normalize
            target_lufs: Target LUFS level
            true_peak_ceiling: Maximum true peak in dBFS
        """
        return _handle_controller_operation(
            f"Normalize track {track_index} to {target_lufs} LUFS",
            controller.analysis.loudness.normalize_track_lufs,
            track_index,
            target_lufs,
            true_peak_ceiling
        )

    @mcp.tool("match_loudness_between_tracks")
    def match_loudness_between_tracks(
        ctx: Context,
        source_track: int,
        target_track: int,
        mode: str = "lufs"
    ) -> Dict[str, Any]:
        """
        Match loudness between two tracks.
        
        Args:
            source_track: Track index to adjust
            target_track: Track index to match
            mode: Matching mode (lufs or spectrum)
        """
        return _handle_controller_operation(
            f"Match loudness of track {source_track} to track {target_track}",
            controller.analysis.loudness.match_loudness_between_tracks,
            source_track,
            target_track,
            mode
        )

    @mcp.tool("write_volume_automation_to_target_lufs")
    def write_volume_automation_to_target_lufs(
        ctx: Context,
        track_index: int,
        target_lufs: float = -23.0,
        smoothing_ms: float = 100.0
    ) -> Dict[str, Any]:
        """
        Generate volume automation to achieve target LUFS without clipping.
        
        Args:
            track_index: Index of track to automate
            target_lufs: Target LUFS level
            smoothing_ms: Automation smoothing time in milliseconds
        """
        return _handle_controller_operation(
            f"Write volume automation for track {track_index} to {target_lufs} LUFS",
            controller.analysis.write_volume_automation_to_target_lufs,
            track_index,
            target_lufs,
            smoothing_ms
        )

    @mcp.tool("clip_gain_adjust")
    def clip_gain_adjust(
        ctx: Context,
        track_index: int,
        item_id: int,
        gain_db: float
    ) -> Dict[str, Any]:
        """
        Adjust clip gain on an audio item without affecting track fader.
        
        Args:
            track_index: Index of track containing the item
            item_id: ID of the item to adjust
            gain_db: Gain adjustment in dB
        """
        return _handle_controller_operation(
            f"Adjust clip gain on track {track_index} item {item_id} by {gain_db:+.1f}dB",
            controller.analysis.clip_gain_adjust,
            track_index,
            item_id,
            gain_db
        )

    @mcp.tool("comprehensive_track_analysis")
    def comprehensive_track_analysis(
        ctx: Context,
        track_index: int,
        window_sec: float = 5.0
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including loudness, spectrum, stereo, and dynamics.
        
        Args:
            track_index: Index of track to analyze
            window_sec: Analysis window in seconds
        """
        try:
            analysis = controller.analysis.comprehensive_track_analysis(track_index, window_sec)
            if analysis:
                return _create_success_response(f"Comprehensive analysis for track {track_index}: {analysis}")
            else:
                return _create_error_response("Failed to perform comprehensive analysis")
        except Exception as e:
            logger.error(f"Failed to perform comprehensive analysis: {e}")
            return _create_error_response(f"Failed to perform comprehensive analysis: {str(e)}")

    @mcp.tool("master_chain_analysis")
    def master_chain_analysis(
        ctx: Context,
        window_sec: float = 10.0
    ) -> Dict[str, Any]:
        """
        Analyze master chain for broadcast/streaming compliance and quality.
        
        Args:
            window_sec: Analysis window in seconds
        """
        try:
            analysis = controller.analysis.master_chain_analysis(window_sec)
            if analysis:
                return _create_success_response(f"Master chain analysis: {analysis}")
            else:
                return _create_error_response("Failed to analyze master chain")
        except Exception as e:
            logger.error(f"Failed to analyze master chain: {e}")
            return _create_error_response(f"Failed to analyze master chain: {str(e)}")


