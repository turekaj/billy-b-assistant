import os
import threading
from app import create_app
from app.core_imports import core_config

# Detect audio devices early so MIC_DEVICE_INDEX and channels are set before sessions start
from core.audio import detect_devices
detect_devices()

# Initialize user manager to load default user and persona
from core.profile_manager import user_manager


user_manager.load_default_user()

# Enable test mode if TEST_MODE environment variable is set
if os.getenv("TEST_MODE", "").lower() == "true":
    from core import test_mode
    test_mode.enable_test_mode()
    from core.logger import logger
    logger.info("Test mode enabled via TEST_MODE environment variable", "🧪")

    # Start the button loop in a background thread so virtual button handlers work
    def start_button_loop():
        try:
            import core.button
            core.button.start_loop()
        except Exception as e:
            logger.error(f"Failed to start button loop: {e}")

    button_thread = threading.Thread(target=start_button_loop, daemon=True)
    button_thread.start()
    logger.info("Button loop started in background thread", "🧪")

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(core_config.FLASK_PORT),
        debug=False,
        use_reloader=False,
    )
