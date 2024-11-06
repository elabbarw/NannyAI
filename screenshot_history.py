import os
from datetime import datetime
from PIL import Image
import json
from utils.logger import get_logger

class ScreenshotHistory:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.screenshots_dir = os.path.join("data", "screenshots")
        self.history_file = os.path.join(self.screenshots_dir, "history.json")
        self._ensure_directories()
        self._load_history()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def _load_history(self):
        """Load screenshot history from JSON file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            self.logger.error(f"Failed to load history: {str(e)}")
            self.history = []

    def _save_history(self):
        """Save screenshot history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save history: {str(e)}")

    def save_screenshot(self, image, analysis_results=None):
        """Save a new screenshot with metadata"""
        try:
            timestamp = datetime.now()
            device_info = ''
            if analysis_results and 'device_name' in analysis_results:
                device_info = f"_{analysis_results['device_name']}"
            
            filename = f"screenshot{device_info}_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.screenshots_dir, filename)

            # Save the image
            image.save(filepath)

            # Add entry to history
            entry = {
                'timestamp': timestamp.isoformat(),
                'filename': filename,
                'filepath': filepath,
                'device_id': analysis_results.get('device_id') if analysis_results else None,
                'device_name': analysis_results.get('device_name') if analysis_results else None,
                'analysis': analysis_results or {}
            }
            self.history.append(entry)
            self._save_history()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {str(e)}")
            return False

    def get_history(self, limit=None, offset=0, device_id=None):
        """Get screenshot history entries"""
        entries = self.history
        if device_id:
            entries = [
                entry for entry in entries
                if entry.get('device_id') == device_id
            ]
            
        entries = sorted(
            entries,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        if limit:
            return entries[offset:offset + limit]
        return entries[offset:]

    def get_screenshot(self, filename):
        """Load a specific screenshot"""
        try:
            filepath = os.path.join(self.screenshots_dir, filename)
            if os.path.exists(filepath):
                return Image.open(filepath)
            return None
        except Exception as e:
            self.logger.error(f"Failed to load screenshot: {str(e)}")
            return None

    def delete_screenshot(self, filename):
        """Delete a screenshot and its history entry"""
        try:
            filepath = os.path.join(self.screenshots_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            self.history = [
                entry for entry in self.history
                if entry['filename'] != filename
            ]
            self._save_history()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete screenshot: {str(e)}")
            return False

    def get_device_screenshots(self, device_id):
        """Get screenshots for a specific device"""
        return [
            entry for entry in self.history
            if entry.get('device_id') == device_id
        ]
