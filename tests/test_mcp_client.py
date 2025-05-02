import logging
from reaper_controller import ReaperController

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Create Reaper controller
        controller = ReaperController(debug=True)
        
        # Test basic operations
        logger.info("Testing basic operations...")
        
        # Create a track
        track_index = controller.create_track("Test Track")
        logger.info(f"Created track {track_index}")
        
        # Set track color
        controller.set_track_color(track_index, "#FF0000")
        logger.info(f"Set track {track_index} color to red")
        
        # Add an FX
        fx_index = controller.add_fx(track_index, "ReaEQ")
        logger.info(f"Added ReaEQ to track {track_index} at index {fx_index}")
        
        # Set FX parameter
        controller.set_fx_param(track_index, fx_index, "Gain", 6.0)
        logger.info(f"Set ReaEQ gain to 6.0")
        
        # Set project tempo
        controller.set_tempo(120.0)
        logger.info("Set tempo to 120 BPM")
        
        # Create a region
        region_index = controller.create_region(0.0, 10.0, "Test Region")
        logger.info(f"Created region {region_index}")
        
        # Create a marker
        marker_index = controller.create_marker(5.0, "Test Marker")
        logger.info(f"Created marker {marker_index}")
        
        # Control master track
        controller.set_master_volume(0.8)
        controller.set_master_pan(-0.5)
        logger.info("Set master volume to 0.8 and pan to -0.5")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        raise

if __name__ == "__main__":
    main()