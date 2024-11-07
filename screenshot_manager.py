import threading
import time
from datetime import datetime
import os
from utils.logger import get_logger
from PIL import Image, ImageGrab
import platform
import io
from screenshot_history import ScreenshotHistory
from device_manager import DeviceManager
from content_analyzer import ContentAnalyzer
from program_terminator import ProgramTerminator

class ScreenshotManager:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.device_manager = DeviceManager()
        self.monitoring = False
        self.monitor_threads = {}
        self.debug_mode = False

        # Initialize platform-specific screenshot methods
        self._screenshot_methods = []
        self._init_screenshot_methods()

        self.history_manager = ScreenshotHistory()
        self.content_analyzer = ContentAnalyzer(config)

    def _init_screenshot_methods(self):
        """Initialize available screenshot methods based on platform"""
        system = platform.system().lower()

        # PIL's ImageGrab works on both Windows and macOS
        self._screenshot_methods.append(('pil', self._take_pil_screenshot))

        # X11 method only on Linux
        if system == 'linux':
            try:
                from Xlib import display, X
                self._screenshot_methods.append(('x11', self._take_x11_screenshot))
            except ImportError:
                self.logger.warning("X11 backend not available")

    def _take_x11_screenshot(self):
        """Take screenshot using X11 (Linux only)"""
        try:
            if self.debug_mode:
                self.logger.info("Attempting X11 screenshot")

            from Xlib import display, X
            d = display.Display()
            root = d.screen().root
            geometry = root.get_geometry()

            screenshot = root.get_image(0, 0, geometry.width, geometry.height,
                                      X.ZPixmap, 0xffffffff)

            image = Image.frombytes("RGB", (geometry.width, geometry.height),
                                  screenshot.data, "raw", "BGRX")

            if self.debug_mode:
                self.logger.info("X11 screenshot successful")

            return image
        except Exception as e:
            if self.debug_mode:
                self.logger.error(f"X11 screenshot failed: {str(e)}")
            raise

    def _take_pil_screenshot(self):
        """Take screenshot using PIL ImageGrab (cross-platform)"""
        try:
            if self.debug_mode:
                self.logger.info("Attempting PIL screenshot")

            screenshot = ImageGrab.grab()

            if self.debug_mode:
                self.logger.info("PIL screenshot successful")

            return screenshot
        except Exception as e:
            if self.debug_mode:
                self.logger.error(f"PIL screenshot failed: {str(e)}")
            raise

    def test_screenshot_capability(self, device_id=None):
        """Test if screenshots can be taken"""
        last_error = None
        device = self.device_manager.get_device(device_id) if device_id else None

        for method_name, method in self._screenshot_methods:
            try:
                if self.debug_mode:
                    self.logger.info(f"Testing screenshot method: {method_name}")

                screenshot = method()
                if screenshot:
                    if device:
                        device.config['screenshot_backend'] = method_name
                        self.device_manager.update_device_config(device_id, device.config)
                    if self.debug_mode:
                        self.logger.info(f"Successfully using {method_name} backend")
                    return True, None
            except Exception as e:
                error_msg = f"{method_name} screenshot failed: {str(e)}"
                if self.debug_mode:
                    self.logger.error(error_msg)
                last_error = error_msg

        error_msg = f"No working screenshot method found. Last error: {last_error}"
        if device:
            self.device_manager.set_device_error(device_id, error_msg)
        return False, error_msg

    def take_screenshot(self, device_id=None):
        """Take a screenshot and return the image object"""
        try:
            device = self.device_manager.get_device(device_id) if device_id else None
            backend = device.config.get('screenshot_backend') if device else None

            if not backend:
                success, error = self.test_screenshot_capability(device_id)
                if not success:
                    return None

            method_dict = dict(self._screenshot_methods)
            backend = device.config.get('screenshot_backend') if device else self._screenshot_methods[0][0]
            screenshot = method_dict[backend]()

            if screenshot:
                if device:
                    self.device_manager.set_device_error(device_id, None)
                return screenshot
            raise Exception("Screenshot capture returned None")

        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            self.logger.error(error_msg)
            if device:
                self.device_manager.set_device_error(device_id, error_msg)
            return None

    def start_monitoring(self, device_id=None):
        """Start monitoring for a specific device or all devices"""
        if device_id:
            return self._start_device_monitoring(device_id)
        else:
            success = True
            for device in self.device_manager.get_all_devices():
                if not self._start_device_monitoring(device.device_id):
                    success = False
            return success

    def _start_device_monitoring(self, device_id):
        """Start monitoring for a specific device"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return False

        can_screenshot, error = self.test_screenshot_capability(device_id)
        if not can_screenshot:
            self.logger.error(f"Cannot start monitoring device {device_id}: {error}")
            return False

        if not device.is_active:
            self.device_manager.set_device_status(device_id, True)
            thread = threading.Thread(target=self._monitor_loop, args=(device_id,), daemon=True)
            self.monitor_threads[device_id] = thread
            thread.start()
        return True

    def stop_monitoring(self, device_id=None):
        """Stop monitoring for a specific device or all devices"""
        if device_id:
            return self._stop_device_monitoring(device_id)
        else:
            for device in self.device_manager.get_all_devices():
                self._stop_device_monitoring(device.device_id)

    def _stop_device_monitoring(self, device_id):
        """Stop monitoring for a specific device"""
        device = self.device_manager.get_device(device_id)
        if device and device.is_active:
            self.device_manager.set_device_status(device_id, False)
            if device_id in self.monitor_threads:
                self.monitor_threads[device_id].join(timeout=1.0)
                del self.monitor_threads[device_id]

    def set_debug_mode(self, enabled):
        """Enable or disable debug mode"""
        self.debug_mode = enabled
        if enabled:
            self.logger.info("Debug mode enabled")

    def get_device_backend(self, device_id):
        """Get the screenshot backend for a specific device"""
        device = self.device_manager.get_device(device_id)
        return device.config.get('screenshot_backend') if device else None

    def get_device_error(self, device_id):
        """Get the last error for a specific device"""
        device = self.device_manager.get_device(device_id)
        return device.last_error if device else None

    def _validate_analysis_result(self, category, score):
        """Validate a single analysis result score"""
        try:
            if isinstance(score, str):
                score = score.strip()
                if not score.replace('.', '', 1).isdigit():
                    self.logger.warning(f"Invalid score format for {category}: {score}")
                    return None
                score = float(score)
            elif not isinstance(score, (int, float)):
                self.logger.warning(f"Invalid score type for {category}: {type(score)}")
                return None
            
            score = float(score)
            if not (0 <= score <= 1):
                self.logger.warning(f"Score out of range for {category}: {score}")
                return None

            return score

        except (ValueError, TypeError) as e:
            self.logger.error(f"Error validating score for {category}: {str(e)}")
            return None

    def _process_content_analysis(self, analysis_results, device):
        try:
            # Validate input
            if not analysis_results or not isinstance(analysis_results, dict):
                self.logger.warning("Invalid analysis results format")
                return False

            if 'error' in analysis_results:
                self.logger.warning(f"Analysis error: {analysis_results['error']}")
                return False

            # Get thresholds and categories
            thresholds = self.config.get('content_thresholds', {
                'violence': 0.7,
                'adult': 0.7,
                'hate': 0.7,
                'drugs': 0.7,
                'gambling': 0.7
            })
            
            monitored_categories = self.config.get('monitored_categories', 
                ['violence', 'adult', 'hate', 'drugs','gambling']
            )

            # Check for alerts
            alerts = []
            program_to_terminate = None
            for category in monitored_categories:
                if category not in analysis_results:
                    continue
                    
                try:
                    score = float(analysis_results[category])
                    threshold = float(thresholds.get(category, 0.7))
                    
                    if score >= threshold:
                        alerts.append(f"{category.capitalize()} ({score:.2f})")
                        self.logger.warning(f"Harmful content detected: {category} ({score:.2f})")

                    # Get program name if available
                    if 'program_name' in analysis_results:
                        program_to_terminate = analysis_results['program_name']

                except (ValueError, TypeError) as e:
                    self.logger.error(f"Score validation error for {category}: {str(e)}")
                    continue

            # Terminate program if identified
            if program_to_terminate:
                terminator = ProgramTerminator(self.logger)
                matching_process = terminator.find_matching_process(program_to_terminate)
                
                if matching_process and terminator.safe_to_terminate(matching_process):
                    if terminator.terminate_program(program_to_terminate):
                        alerts.append(f"Terminated program: {matching_process['name']}")
                else:
                    self.logger.warning(f"Could not safely terminate program: {program_to_terminate}")

            # Send notification if needed
            if alerts and hasattr(self, 'notification_mgr'):
                alert_message = f"Alert from {device.name}:\n" + "\n".join(alerts)
                try:
                    self.notification_mgr.send_alert(alert_message)
                except Exception as e:
                    self.logger.error(f"Failed to send notification: {str(e)}")

            return bool(alerts)

        except Exception as e:
            self.logger.error(f"Content analysis processing error: {str(e)}")
            return False

    def _monitor_loop(self, device_id):
        """Main monitoring loop for a specific device"""
        device = self.device_manager.get_device(device_id)
        retry_count = 0
        max_retries = 3

        while device and device.is_active:
            try:
                interval = device.config.get('screenshot_interval',
                                        self.config.get('screenshot_interval', 30))
                screenshot = self.take_screenshot(device_id)

                if screenshot:
                    retry_count = 0

                    try:
                        if self.debug_mode:
                            self.logger.info(f"Analyzing screenshot for device: {device.name}")

                        analysis_results = self.content_analyzer.analyze_image(screenshot)

                        if analysis_results:
                            if isinstance(analysis_results, dict):
                                device_info = {
                                    'device_id': device_id,
                                    'device_name': device.name,
                                    'timestamp': datetime.now().isoformat()
                                }
                                analysis_results.update(device_info)

                                has_alerts = self._process_content_analysis(analysis_results, device)

                                if self.debug_mode:
                                    if has_alerts:
                                        self.logger.info(f"Alerts detected for device: {device.name}")
                                    else:
                                        self.logger.info(f"No alerts for device: {device.name}")

                                self.history_manager.save_screenshot(screenshot, analysis_results)
                            else:
                                self.logger.error(f"Invalid analysis results format: {type(analysis_results)}")
                                error_results = {
                                    'error': 'Invalid analysis format',
                                    'device_id': device_id,
                                    'device_name': device.name,
                                    'timestamp': datetime.now().isoformat()
                                }
                                self.history_manager.save_screenshot(screenshot, error_results)

                    except Exception as e:
                        self.logger.error(f"Content analysis error: {str(e)}")
                        error_results = {
                            'error': str(e),
                            'device_id': device_id,
                            'device_name': device.name,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.history_manager.save_screenshot(screenshot, error_results)

                time.sleep(interval)

            except Exception as e:
                retry_count += 1
                error_msg = f"Monitor loop error for device {device_id}: {str(e)}"
                self.logger.error(error_msg)
                self.device_manager.set_device_error(device_id, error_msg)

                if retry_count >= max_retries:
                    self.logger.error(f"Max retries ({max_retries}) reached for device {device_id}. Stopping monitoring.")
                    self.device_manager.set_device_status(device_id, False)
                    break

                time.sleep(min(5 * retry_count, 30))

            device = self.device_manager.get_device(device_id)