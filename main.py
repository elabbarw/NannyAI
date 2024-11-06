import tkinter as tk
from gui.main_window import MainWindow
from config_manager import ConfigManager
from screenshot_manager import ScreenshotManager
from content_analyzer import ContentAnalyzer
from notification_manager import NotificationManager
from utils.logger import setup_logger

def main():
    # Setup logging
    logger = setup_logger()
    
    # Initialize configuration
    config = ConfigManager()
    
    # Initialize components
    screenshot_mgr = ScreenshotManager(config)
    content_analyzer = ContentAnalyzer(config)
    notification_mgr = NotificationManager(config)
    
    # Setup main GUI window
    root = tk.Tk()
    app = MainWindow(root, config, screenshot_mgr, content_analyzer, notification_mgr)
    
    # Start monitoring if enabled in config
    if config.get('monitoring_enabled', False):
        screenshot_mgr.start_monitoring()
    
    try:
        root.mainloop()
    finally:
        # Cleanup on exit
        if hasattr(app, 'system_tray'):
            app.system_tray.stop()
        screenshot_mgr.stop_monitoring()

if __name__ == "__main__":
    main()
