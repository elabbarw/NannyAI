import os
from utils.logger import get_logger
import json

class Device:
    def __init__(self, device_id, name, config):
        self.device_id = device_id
        self.name = name
        self.config = config
        self.is_active = False
        self.last_screenshot = None
        self.last_error = None

class DeviceManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.devices = {}
        self.devices_file = "data/devices.json"
        self._load_devices()

    def _load_devices(self):
        """Load devices from JSON file"""
        try:
            if os.path.exists(self.devices_file):
                with open(self.devices_file, 'r') as f:
                    devices_data = json.load(f)
                    for device_data in devices_data:
                        device = Device(
                            device_data['device_id'],
                            device_data['name'],
                            device_data.get('config', {})
                        )
                        self.devices[device.device_id] = device
        except Exception as e:
            self.logger.error(f"Failed to load devices: {str(e)}")

    def _save_devices(self):
        """Save devices to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.devices_file), exist_ok=True)
            devices_data = [
                {
                    'device_id': device.device_id,
                    'name': device.name,
                    'config': device.config
                }
                for device in self.devices.values()
            ]
            with open(self.devices_file, 'w') as f:
                json.dump(devices_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save devices: {str(e)}")

    def add_device(self, name, config=None):
        """Add a new device"""
        device_id = f"device_{len(self.devices) + 1}"
        device = Device(device_id, name, config or {})
        self.devices[device_id] = device
        self._save_devices()
        return device

    def remove_device(self, device_id):
        """Remove a device"""
        if device_id in self.devices:
            del self.devices[device_id]
            self._save_devices()
            return True
        return False

    def get_device(self, device_id):
        """Get a device by ID"""
        return self.devices.get(device_id)

    def get_all_devices(self):
        """Get all devices"""
        return list(self.devices.values())

    def update_device_config(self, device_id, config):
        """Update device configuration"""
        if device_id in self.devices:
            self.devices[device_id].config = config
            self._save_devices()
            return True
        return False

    def set_device_status(self, device_id, is_active):
        """Set device active status"""
        if device_id in self.devices:
            self.devices[device_id].is_active = is_active
            return True
        return False

    def set_device_error(self, device_id, error):
        """Set device error message"""
        if device_id in self.devices:
            self.devices[device_id].last_error = error
            return True
        return False
