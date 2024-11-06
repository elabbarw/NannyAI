from screenshot_manager import ScreenshotManager
from PIL import Image
import io
from utils.logger import get_logger
from vncdotool import api

class VNCDeviceMonitor:
    def __init__(self, device_id, device_config):
        self.device_id = device_id
        self.config = device_config
        self.logger = get_logger(__name__)
        self.client = None

    async def connect(self):
        """Connect to VNC server"""
        try:
            host = self.config.get('vnc_host')
            port = self.config.get('vnc_port', 5900)
            password = self.config.get('vnc_password')

            if not (host and password):
                raise ValueError("VNC host and password are required")

            connection_string = f"vnc://{host}:{port}"
            self.client = await api.connect(connection_string, password=password)
            return True
        except Exception as e:
            self.logger.error(f"VNC connection failed: {str(e)}")
            return False

    async def capture_screenshot(self):
        """Capture screenshot from VNC connection"""
        try:
            if not self.client:
                if not await self.connect():
                    return None

            # Capture screenshot
            png_data = await self.client.capture()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(png_data))
            return image

        except Exception as e:
            self.logger.error(f"VNC screenshot failed: {str(e)}")
            await self.disconnect()
            return None

    async def disconnect(self):
        """Disconnect from VNC server"""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                self.logger.error(f"VNC disconnect error: {str(e)}")
            finally:
                self.client = None
