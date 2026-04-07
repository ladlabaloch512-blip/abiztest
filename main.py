import sys
import eel
from src.utils.logger import get_logger

# Import the bridge so Eel knows about the exposed functions
import src.api.bridge

logger = get_logger("MainApp")

from src.core.licensing import LicenseManager

def main():
    logger.info("Starting FB Marketplace Manager Pro (Web UI)")

    # Initialize Eel with the 'web' folder
    eel.init('web')

    # Check license
    license_manager = LicenseManager()
    is_valid, msg = license_manager.check_license()

    start_page = 'index.html' if is_valid else 'license.html'
    if not is_valid:
        logger.warning(f"License check failed: {msg}")
    else:
        logger.info(f"License check passed: {msg}")

    # Start the application
    try:
        # We use a large geometry to match the previous desktop feel
        eel.start(start_page, size=(1200, 800), port=0)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        logger.info("Application closed.")

if __name__ == "__main__":
    main()
