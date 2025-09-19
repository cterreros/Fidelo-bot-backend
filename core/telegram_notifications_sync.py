"""
Synchronous Telegram notification system for FideloBot
More robust alternative that doesn't have asyncio issues
"""
import logging
import requests
from datetime import date
from django.conf import settings
from .models import Client, Purchase, LoyaltyAccount, Business, PointEvent

logger = logging.getLogger(__name__)


class SyncTelegramNotificationService:
    """Synchronous service for sending Telegram notifications"""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id: str, text: str, parse_mode: str = 'Markdown'):
        """Send message using requests (synchronous)"""
        url = f"{self.base_url}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False

    def send_purchase_notification(self, telegram_user_id: str, client_id: str,
                                 purchase_id: str, is_new_client: bool = False):
        """Send notification when a purchase is made"""
        try:
            # Get data from database
            client = Client.objects.get(client_id=client_id)
            purchase = Purchase.objects.get(purchase_id=purchase_id)
            account = LoyaltyAccount.objects.get(client=client)
            business = client.business

            # Calculate points earned
            points_earned = int(purchase.amount * business.points_per_currency)

            # Create message based on whether client is new or existing
            if is_new_client:
                message = f"""
🎉 ¡Bienvenido a {business.name}!

¡Te hemos registrado automáticamente en nuestro programa de lealtad!

🛍️ **Tu compra:**
• Monto: ${purchase.amount} {purchase.currency}
• Fecha: {purchase.purchased_at.strftime('%d/%m/%Y %H:%M')}

💎 **Puntos ganados:** +{points_earned} pts
💰 **Balance actual:** {account.points_balance} pts

🎁 **Programa de lealtad:**
• Ganas {business.points_per_currency} puntos por cada peso gastado
• Recibes {business.birthday_bonus_points} puntos gratis en tu cumpleaños

¡Gracias por tu compra! 🙏
                """
            else:
                message = f"""
🛍️ **Nueva compra en {business.name}**

• Monto: ${purchase.amount} {purchase.currency}
• Fecha: {purchase.purchased_at.strftime('%d/%m/%Y %H:%M')}

💎 **Puntos ganados:** +{points_earned} pts
💰 **Balance actual:** {account.points_balance} pts

¡Gracias por tu compra! 🙏

Usa /points para ver tu balance completo.
                """

            success = self.send_message(telegram_user_id, message.strip())

            if success:
                logger.info(f"Purchase notification sent to {telegram_user_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending purchase notification: {e}")
            return False

    def send_birthday_notification(self, telegram_user_id: str, client_id: str):
        """Send birthday notification with bonus points"""
        try:
            client = Client.objects.get(client_id=client_id)
            business = client.business
            account = LoyaltyAccount.objects.get(client=client)

            message = f"""
🎂 ¡FELIZ CUMPLEAÑOS {client.name}! 🎉

{business.name} te desea un día increíble lleno de alegría.

🎁 **Regalo de cumpleaños:**
• +{business.birthday_bonus_points} puntos gratis
• Balance actualizado: {account.points_balance} pts

¡Que tengas un cumpleaños maravilloso! 🥳🎈

Usa /points para ver todos tus puntos.
            """

            success = self.send_message(telegram_user_id, message.strip())

            if success:
                logger.info(f"Birthday notification sent to {telegram_user_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending birthday notification: {e}")
            return False

    def send_points_update_notification(self, telegram_user_id: str, client_id: str,
                                      points_change: int, reason: str):
        """Send notification for manual points adjustments"""
        try:
            client = Client.objects.get(client_id=client_id)
            business = client.business
            account = LoyaltyAccount.objects.get(client=client)

            emoji = "➕" if points_change > 0 else "➖"
            action = "ganado" if points_change > 0 else "usado"

            message = f"""
💎 **Actualización de puntos - {business.name}**

{emoji} **Has {action} {abs(points_change)} puntos**
💰 **Balance actual:** {account.points_balance} pts

📝 **Motivo:** {reason}

Usa /points para ver tu historial completo.
            """

            success = self.send_message(telegram_user_id, message.strip())

            if success:
                logger.info(f"Points update notification sent to {telegram_user_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending points update notification: {e}")
            return False


# Singleton instance
sync_notification_service = SyncTelegramNotificationService()


# Public functions for easy use
def send_purchase_notification(telegram_user_id: str, client_id: str,
                             purchase_id: str, is_new_client: bool = False):
    """Send purchase notification using sync service"""
    return sync_notification_service.send_purchase_notification(
        telegram_user_id, client_id, purchase_id, is_new_client
    )


def send_birthday_notification(telegram_user_id: str, client_id: str):
    """Send birthday notification using sync service"""
    return sync_notification_service.send_birthday_notification(
        telegram_user_id, client_id
    )


def send_points_update_notification(telegram_user_id: str, client_id: str,
                                  points_change: int, reason: str):
    """Send points update notification using sync service"""
    return sync_notification_service.send_points_update_notification(
        telegram_user_id, client_id, points_change, reason
    )


def check_and_send_birthday_notifications():
    """Check for clients with birthdays today and send notifications (sync version)"""
    today = date.today()

    # Find clients with birthdays today
    birthday_clients = Client.objects.filter(
        birthday__month=today.month,
        birthday__day=today.day
    ).select_related('business')

    notifications_sent = 0

    for client in birthday_clients:
        try:
            # Award birthday bonus
            from .services import PointsService
            PointsService.award_birthday_bonus(client)

            # Try to find telegram user ID
            if client.email.startswith('telegram_') and client.email.endswith('@fidelo.local'):
                telegram_user_id = client.email.replace('telegram_', '').replace('@fidelo.local', '')

                # Send notification
                success = send_birthday_notification(telegram_user_id, str(client.client_id))
                if success:
                    notifications_sent += 1

        except Exception as e:
            logger.error(f"Error processing birthday for client {client.client_id}: {e}")
            continue

    logger.info(f"Birthday notifications processed: {notifications_sent} sent")
    return notifications_sent