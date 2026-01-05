"""
Volume Mount Controller - Main entry point

Orchestrates volume mount monitoring and recovery in Kubernetes.
"""

import os
import sys
import signal
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from controller import VolumeMountController
from logger import setup_logging


def main():
    """Main entry point for the application."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logging(log_level)
    
    logger.info("Starting Volume Mount Controller")
    logger.info(f"Python version: {sys.version}")
    
    try:
        # Create controller instance
        controller = VolumeMountController()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            controller.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start monitoring
        logger.info("Starting volume mount monitoring...")
        controller.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
