import pystray
from PIL import Image
import threading
import os

class SystemTrayIcon:
    def __init__(self, main_window):
        self.main_window = main_window
        self.icon = None
        
    def create_icon(self):
        """Create and run system tray icon"""
        # Create or load icon image
        icon_path = "generated-icon.png"
        if not os.path.exists(icon_path):
            # Create a simple icon if none exists
            image = Image.new('RGB', (64, 64), color='blue')
        else:
            image = Image.open(icon_path)

        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", self._toggle_window),
            pystray.MenuItem("Start All", self._start_all),
            pystray.MenuItem("Stop All", self._stop_all),
            pystray.MenuItem("Exit", self._quit)
        )

        self.icon = pystray.Icon(
            "nannyai",
            image,
            "NannyAI",
            menu
        )

    def run(self):
        """Run the system tray icon in a separate thread"""
        self.create_icon()
        icon_thread = threading.Thread(target=self.icon.run)
        icon_thread.daemon = True
        icon_thread.start()

    def _toggle_window(self, _=None):
        """Toggle main window visibility"""
        if self.main_window.root.state() == 'withdrawn':
            self.main_window.root.deiconify()
            self.main_window.root.lift()
        else:
            self.main_window.root.withdraw()

    def _start_all(self, _=None):
        """Start all monitoring"""
        self.main_window._start_all_monitoring()

    def _stop_all(self, _=None):
        """Stop all monitoring"""
        self.main_window._stop_all_monitoring()

    def _quit(self, _=None):
        """Quit the application"""
        self.icon.stop()
        self.main_window.root.quit()

    def stop(self):
        """Stop the system tray icon"""
        if self.icon:
            self.icon.stop()
