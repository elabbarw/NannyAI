import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import get_logger

class NotificationManager:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

    def send_alert(self, message, screenshot_path=None):
        """Send email alert to configured parent email"""
        try:
            email_config = self.config.get('email_settings', {})
            if not email_config:
                self.logger.error("Email settings not configured")
                return False

            msg = MIMEMultipart()
            msg['From'] = email_config.get('sender_email')
            msg['To'] = email_config.get('parent_email')
            msg['Subject'] = "NannyAI - Content Alert - Screen Monitor"

            body = f"Alert: {message}"
            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server and send email
            with smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port')) as server:
                server.starttls()
                server.login(
                    email_config.get('sender_email'),
                    email_config.get('sender_password')
                )
                server.send_message(msg)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False
