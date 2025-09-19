"""
SMS Service for FideloBot
Supports both simulation (free) and real SMS (Twilio)
"""
import logging
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service with development/production modes"""

    def __init__(self):
        self.mode = getattr(settings, 'SMS_MODE', 'development')
        self.twilio_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.twilio_phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

    def send_purchase_notification_sms(self, client_phone, client_name, business_name,
                                     points_earned, total_points, bot_username=None):
        """Send SMS notification for a new purchase"""

        message = f"""¡Ganaste {points_earned} puntos en {business_name}!
Balance: {total_points} pts
Busca @{bot_username or 'FideloBot'} en Telegram
Vincula con: /link_telegram {client_phone}"""

        return self.send_sms(client_phone, message)

    def send_sms(self, phone_number, message):
        """Send SMS - development mode logs, production mode uses Twilio"""

        if self.mode == 'development':
            return self._simulate_sms(phone_number, message)
        elif self.mode == 'production':
            return self._send_real_sms(phone_number, message)
        else:
            logger.error(f"Invalid SMS_MODE: {self.mode}")
            return False

    def _simulate_sms(self, phone_number, message):
        """Simulate SMS for development (free)"""
        try:
            # Log to console with nice formatting
            print("\n" + "="*60)
            print("📱 SMS SIMULATION")
            print("="*60)
            print(f"📞 To: {phone_number}")
            print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("📄 Message:")
            print("-" * 40)
            print(message)
            print("="*60)

            logger.info(f"SMS simulated to {phone_number}")
            return True

        except Exception as e:
            logger.error(f"Error simulating SMS: {e}")
            return False

    def _send_real_sms(self, phone_number, message):
        """Send real SMS using Twilio"""
        try:
            from twilio.rest import Client as TwilioClient

            if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
                logger.error("Twilio credentials not configured")
                return False

            client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)

            message_obj = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )

            logger.info(f"SMS sent successfully to {phone_number}, SID: {message_obj.sid}")
            print(f"✅ SMS REAL enviado a {phone_number}")
            print(f"📋 Twilio SID: {message_obj.sid}")

            return True

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            print(f"❌ Error enviando SMS: {e}")
            return False


# Global SMS service instance
sms_service = SMSService()