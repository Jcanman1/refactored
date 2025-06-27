import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from .settings import load_email_settings, DEFAULT_EMAIL_SETTINGS

logger = logging.getLogger(__name__)

# Load SMTP configuration once at import time
email_settings = load_email_settings()


def send_threshold_email(sensitivity_num: int, is_high: bool = True) -> bool:
    """Send an email notification for a threshold violation."""
    try:
        from .callbacks import threshold_settings  # runtime import to avoid cycle

        email_address = threshold_settings.get("email_address", "")
        if not email_address:
            logger.warning("No email address configured for notifications")
            return False

        msg = MIMEMultipart()
        msg["Subject"] = "Enpresor Alarm"
        msg["From"] = "jcantu@satake-usa.com"
        msg["To"] = email_address

        threshold_type = "upper" if is_high else "lower"
        body = f"Sensitivity {sensitivity_num} has reached the {threshold_type} threshold."
        msg.attach(MIMEText(body, "plain"))

        logger.info(f"Sending email to {email_address}: {body}")

        server_addr = email_settings.get("smtp_server", DEFAULT_EMAIL_SETTINGS["smtp_server"])
        port = email_settings.get("smtp_port", DEFAULT_EMAIL_SETTINGS["smtp_port"])
        server = smtplib.SMTP(server_addr, port)
        server.starttls()
        username = email_settings.get("smtp_username")
        password = email_settings.get("smtp_password")
        if username and password:
            server.login(username, password)

        from_addr = email_settings.get("from_address", DEFAULT_EMAIL_SETTINGS["from_address"])
        text = msg.as_string()
        server.sendmail(from_addr, email_address, text)
        server.quit()
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error sending threshold email: {e}")
        return False
