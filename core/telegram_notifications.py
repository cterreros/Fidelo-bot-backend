"""
Telegram notification system for FideloBot
Handles all outbound notifications to users
"""
import logging
import asyncio
from datetime import date
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import Client, Purchase, LoyaltyAccount, Business, PointEvent

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Service for sending Telegram notifications"""

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def send_purchase_notification(self, telegram_user_id: str, client_id: str,
                                       purchase_id: str, is_new_client: bool = False):
        """
        Send notification when a purchase is made
        """
        try:
            # Get data from database
            client = await sync_to_async(Client.objects.get)(client_id=client_id)
            purchase = await sync_to_async(Purchase.objects.get)(purchase_id=purchase_id)
            account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
            business = await sync_to_async(lambda: client.business)()

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

            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=message.strip(),
                parse_mode='Markdown'
            )

            logger.info(f"Purchase notification sent to {telegram_user_id}")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification to {telegram_user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending purchase notification: {e}")
            return False

    async def send_birthday_notification(self, telegram_user_id: str, client_id: str):
        """
        Send birthday notification with bonus points
        """
        try:
            client = await sync_to_async(Client.objects.get)(client_id=client_id)
            business = await sync_to_async(lambda: client.business)()
            account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)

            message = f"""
🎂 ¡FELIZ CUMPLEAÑOS {client.name}! 🎉

{business.name} te desea un día increíble lleno de alegría.

🎁 **Regalo de cumpleaños:**
• +{business.birthday_bonus_points} puntos gratis
• Balance actualizado: {account.points_balance} pts

¡Que tengas un cumpleaños maravilloso! 🥳🎈

Usa /points para ver todos tus puntos.
            """

            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=message.strip(),
                parse_mode='Markdown'
            )

            logger.info(f"Birthday notification sent to {telegram_user_id}")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send birthday notification to {telegram_user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending birthday notification: {e}")
            return False

    async def send_points_update_notification(self, telegram_user_id: str, client_id: str,
                                            points_change: int, reason: str):
        """
        Send notification for manual points adjustments
        """
        try:
            client = await sync_to_async(Client.objects.get)(client_id=client_id)
            business = await sync_to_async(lambda: client.business)()
            account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)

            emoji = "➕" if points_change > 0 else "➖"
            action = "ganado" if points_change > 0 else "usado"

            message = f"""
💎 **Actualización de puntos - {business.name}**

{emoji} **Has {action} {abs(points_change)} puntos**
💰 **Balance actual:** {account.points_balance} pts

📝 **Motivo:** {reason}

Usa /points para ver tu historial completo.
            """

            await self.bot.send_message(
                chat_id=telegram_user_id,
                text=message.strip(),
                parse_mode='Markdown'
            )

            logger.info(f"Points update notification sent to {telegram_user_id}")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send points update notification to {telegram_user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending points update notification: {e}")
            return False


# Singleton instance
notification_service = TelegramNotificationService()


# Helper functions for async tasks
def send_purchase_notification(telegram_user_id: str, client_id: str,
                             purchase_id: str, is_new_client: bool = False):
    """
    Sync wrapper for sending purchase notifications
    Can be used with Celery or direct calls
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            notification_service.send_purchase_notification(
                telegram_user_id, client_id, purchase_id, is_new_client
            )
        )
    finally:
        loop.close()


def send_birthday_notification(telegram_user_id: str, client_id: str):
    """
    Sync wrapper for sending birthday notifications
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            notification_service.send_birthday_notification(telegram_user_id, client_id)
        )
    finally:
        loop.close()


def send_points_update_notification(telegram_user_id: str, client_id: str,
                                  points_change: int, reason: str):
    """
    Sync wrapper for sending points update notifications
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            notification_service.send_points_update_notification(
                telegram_user_id, client_id, points_change, reason
            )
        )
    finally:
        loop.close()


# Birthday checker function
def check_and_send_birthday_notifications():
    """
    Check for clients with birthdays today and send notifications
    This function should be called daily (e.g., via cron job or Celery beat)
    """
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
            # First check if client email follows telegram pattern
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