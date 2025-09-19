"""
Advanced bot features for FideloBot
Includes admin commands, client linking, and enhanced menus
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
from core.models import Business, Client, LoyaltyAccount, PointEvent
from core.services import PointsService

logger = logging.getLogger(__name__)


class AdvancedBotFeatures:
    """Advanced features for the FideloBot"""

    @staticmethod
    async def link_telegram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Command for businesses to link Telegram users to existing clients
        Usage: /link_telegram client_email
        """
        if not context.args:
            await update.message.reply_text(
                "❌ **Uso correcto:**\n"
                "`/link_telegram email@cliente.com`\n"
                "`/link_telegram +529511577551`\n\n"
                "Este comando vincula tu Telegram con un cliente existente usando email o teléfono.",
                parse_mode='Markdown'
            )
            return

        user = update.effective_user
        telegram_id = user.id
        client_email = context.args[0]

        try:
            # Find client by email or phone
            clients = await sync_to_async(list)(
                Client.objects.filter(email=client_email)
            )

            # If no clients found by email, try phone
            if not clients and (client_email.startswith('+') or client_email.isdigit()):
                clients = await sync_to_async(list)(
                    Client.objects.filter(phone=client_email)
                )

            if not clients:
                await update.message.reply_text(
                    f"❌ No se encontró ningún cliente con: `{client_email}`\n\n"
                    "Verifica que el email o teléfono sea correcto o contacta al negocio.",
                    parse_mode='Markdown'
                )
                return

            if len(clients) > 1:
                # Multiple clients with same email across businesses
                message = f"📋 **Encontrados {len(clients)} clientes con email `{client_email}`:**\n\n"

                keyboard = []
                for i, client in enumerate(clients):
                    business_name = await sync_to_async(lambda: client.business.name)()
                    message += f"{i+1}. **{business_name}** - {client.name}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"Vincular con {business_name}",
                            callback_data=f"link_{client.client_id}_{telegram_id}"
                        )
                    ])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

            else:
                # Single client found
                client = clients[0]
                await AdvancedBotFeatures._complete_telegram_link(update, client, telegram_id)

        except Exception as e:
            logger.error(f"Error in link_telegram_command: {e}")
            await update.message.reply_text("❌ Error procesando la vinculación. Intenta de nuevo.")

    @staticmethod
    async def handle_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle client linking from inline keyboard"""
        query = update.callback_query
        await query.answer()

        try:
            # Parse callback data: link_{client_id}_{telegram_id}
            _, client_id, telegram_id = query.data.split('_')

            client = await sync_to_async(Client.objects.get)(client_id=client_id)
            await AdvancedBotFeatures._complete_telegram_link(query, client, telegram_id)

        except Exception as e:
            logger.error(f"Error in handle_link_callback: {e}")
            await query.edit_message_text("❌ Error completando la vinculación.")

    @staticmethod
    async def _complete_telegram_link(update_or_query, client, telegram_id):
        """Complete the Telegram linking process"""
        try:
            # Update client email to include Telegram ID
            old_email = client.email
            client.email = f"telegram_{telegram_id}@fidelo.local"
            await sync_to_async(client.save)()

            # Get client data
            business_name = await sync_to_async(lambda: client.business.name)()
            account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)

            success_message = f"""
✅ **¡Vinculación exitosa!**

🏪 **Negocio:** {business_name}
👤 **Cliente:** {client.name}
📧 **Email original:** {old_email}
💎 **Puntos actuales:** {account.points_balance} pts

Ahora recibirás notificaciones automáticas cuando:
• Realices compras y ganes puntos
• Sea tu cumpleaños
• Haya promociones especiales

¡Usa /points para ver tu balance! 🎉
            """

            if hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(success_message, parse_mode='Markdown')
            else:
                await update_or_query.message.reply_text(success_message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error completing link: {e}")
            error_message = "❌ Error completando la vinculación."

            if hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(error_message)
            else:
                await update_or_query.message.reply_text(error_message)

    @staticmethod
    async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enhanced points command with detailed breakdown"""
        user = update.effective_user
        telegram_id = user.id

        try:
            clients = await sync_to_async(list)(
                Client.objects.filter(email=f"telegram_{telegram_id}@fidelo.local")
            )

            if not clients:
                await update.message.reply_text(
                    "🚫 No estás registrado en ningún negocio.\n\n"
                    "Opciones:\n"
                    "• Usa /start para registrarte\n"
                    "• Usa /link_telegram para vincular tu cuenta existente\n"
                    "• Contacta al negocio para más ayuda"
                )
                return

            message = "💎 **Tu Balance de Puntos:**\n\n"
            total_points = 0

            for client in clients:
                try:
                    business_name = await sync_to_async(lambda: client.business.name)()
                    account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)

                    message += f"🏪 **{business_name}**\n"
                    message += f"   💰 Balance: **{account.points_balance}** pts\n"

                    # Get recent point events
                    recent_events = await sync_to_async(list)(
                        PointEvent.objects.filter(client=client).order_by('-occurred_at')[:3]
                    )

                    if recent_events:
                        message += "   📊 Últimas actividades:\n"
                        for event in recent_events:
                            sign = "+" if event.points > 0 else ""
                            source_emoji = {
                                'purchase': '🛍️',
                                'birthday': '🎂',
                                'adjustment': '⚙️'
                            }.get(event.source, '📝')
                            message += f"      {source_emoji} {sign}{event.points} pts - {event.get_source_display()}\n"

                    message += "\n"
                    total_points += account.points_balance

                except LoyaltyAccount.DoesNotExist:
                    business_name = await sync_to_async(lambda: client.business.name)()
                    message += f"🏪 **{business_name}**\n"
                    message += "   💰 Balance: **0** pts\n\n"

            if len(clients) > 1:
                message += f"🎯 **Total en todos los negocios:** {total_points} pts\n\n"

            # Add action buttons
            keyboard = [
                [InlineKeyboardButton("📊 Historial Completo", callback_data="full_history")],
                [InlineKeyboardButton("🎁 Programas de Lealtad", callback_data="loyalty_programs")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in points_command: {e}")
            await update.message.reply_text("❌ Error consultando tus puntos.")

    @staticmethod
    async def loyalty_programs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show detailed loyalty program information"""
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        telegram_id = user.id

        try:
            clients = await sync_to_async(list)(
                Client.objects.filter(email=f"telegram_{telegram_id}@fidelo.local")
            )

            if not clients:
                await query.edit_message_text("🚫 No estás registrado en ningún programa.")
                return

            message = "🎁 **Tus Programas de Lealtad:**\n\n"

            for client in clients:
                business = await sync_to_async(lambda: client.business)()
                account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)

                message += f"🏪 **{business.name}**\n"
                message += f"   👤 Miembro desde: {client.joined_at.strftime('%d/%m/%Y')}\n"
                message += f"   💎 Puntos actuales: {account.points_balance}\n"
                message += f"   💰 Ganancia: {business.points_per_currency} pts por peso\n"
                message += f"   🎂 Bonus cumpleaños: {business.birthday_bonus_points} pts\n"

                if client.birthday:
                    message += f"   📅 Tu cumpleaños: {client.birthday.strftime('%d de %B')}\n"

                message += "\n"

            keyboard = [
                [InlineKeyboardButton("⬅️ Volver a Puntos", callback_data="back_to_points")],
                [InlineKeyboardButton("📝 Actualizar Datos", callback_data="update_profile")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in loyalty_programs_callback: {e}")
            await query.edit_message_text("❌ Error cargando programas de lealtad.")

    @staticmethod
    async def update_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle profile update requests"""
        query = update.callback_query
        await query.answer()

        message = """
📝 **Actualizar tu Perfil**

¿Qué información quieres actualizar?

💡 **Tip:** Mantener tu información actualizada te permite recibir mejores beneficios.
        """

        keyboard = [
            [InlineKeyboardButton("📅 Fecha de Cumpleaños", callback_data="update_birthday")],
            [InlineKeyboardButton("📱 Número de Teléfono", callback_data="update_phone")],
            [InlineKeyboardButton("👤 Nombre", callback_data="update_name")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="loyalty_programs")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    @staticmethod
    async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show notification settings and test"""
        user = update.effective_user
        telegram_id = user.id

        message = f"""
🔔 **Configuración de Notificaciones**

🆔 **Tu Telegram ID:** `{telegram_id}`

📬 **Recibes notificaciones automáticas cuando:**
• Realizas compras y ganas puntos 🛍️
• Es tu cumpleaños 🎂
• Hay promociones especiales 🎉

💡 **Para vincular tu cuenta:**
Proporciona este ID al negocio o usa `/link_telegram email@tumail.com`

🧪 **¿Quieres probar las notificaciones?**
        """

        keyboard = [
            [InlineKeyboardButton("🧪 Enviar Notificación de Prueba", callback_data="test_notification")],
            [InlineKeyboardButton("📋 Ver Clientes Vinculados", callback_data="linked_clients")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    @staticmethod
    async def test_notification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a test notification"""
        query = update.callback_query
        await query.answer("🧪 Enviando notificación de prueba...")

        test_message = """
🧪 **Notificación de Prueba - FideloBot**

¡Perfecto! Las notificaciones están funcionando correctamente.

Recibirás mensajes como este cuando:
• Ganes puntos por compras
• Sea tu cumpleaños
• Haya ofertas especiales

✅ Tu Telegram está configurado correctamente.
        """

        await query.message.reply_text(test_message, parse_mode='Markdown')

    @staticmethod
    async def admin_send_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Admin command to manually award points
        Usage: /admin_points client_email points reason
        """
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ **Uso correcto:**\n"
                "`/admin_points email@cliente.com 50 Promoción especial`\n\n"
                "⚠️ Comando administrativo",
                parse_mode='Markdown'
            )
            return

        client_email = context.args[0]
        try:
            points = int(context.args[1])
            reason = ' '.join(context.args[2:])
        except ValueError:
            await update.message.reply_text("❌ Los puntos deben ser un número entero.")
            return

        try:
            # Find client
            client = await sync_to_async(Client.objects.get)(email=client_email)

            # Award points
            account = await sync_to_async(PointsService.manual_adjustment)(
                client, points, reason
            )

            # Try to send notification if client has Telegram
            notification_sent = False
            if client.email.startswith('telegram_') and client.email.endswith('@fidelo.local'):
                telegram_user_id = client.email.replace('telegram_', '').replace('@fidelo.local', '')
                try:
                    from core.telegram_notifications import send_points_update_notification
                    notification_sent = send_points_update_notification(
                        telegram_user_id, str(client.client_id), points, reason
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")

            await update.message.reply_text(
                f"✅ **Puntos otorgados:**\n\n"
                f"👤 Cliente: {client.name}\n"
                f"💎 Puntos: +{points}\n"
                f"📝 Motivo: {reason}\n"
                f"💰 Nuevo balance: {account.points_balance}\n"
                f"📬 Notificación enviada: {'Sí' if notification_sent else 'No'}",
                parse_mode='Markdown'
            )

        except Client.DoesNotExist:
            await update.message.reply_text(f"❌ Cliente no encontrado: {client_email}")
        except Exception as e:
            logger.error(f"Error in admin_send_points: {e}")
            await update.message.reply_text("❌ Error otorgando puntos.")


# Export functions for easy import
link_telegram_command = AdvancedBotFeatures.link_telegram_command
handle_link_callback = AdvancedBotFeatures.handle_link_callback
points_command = AdvancedBotFeatures.points_command
loyalty_programs_callback = AdvancedBotFeatures.loyalty_programs_callback
update_profile_callback = AdvancedBotFeatures.update_profile_callback
notifications_command = AdvancedBotFeatures.notifications_command
test_notification_callback = AdvancedBotFeatures.test_notification_callback
admin_send_points = AdvancedBotFeatures.admin_send_points