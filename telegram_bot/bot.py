import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from django.conf import settings
from asgiref.sync import sync_to_async
from core.models import Business, Client, LoyaltyAccount, Purchase
from core.services import ClientService, PurchaseService, PointsService
from .advanced_bot_features import (
    link_telegram_command, handle_link_callback, points_command,
    loyalty_programs_callback, update_profile_callback, notifications_command,
    test_notification_callback, admin_send_points, show_history_callback,
    back_to_points_callback
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class FideloBot:
    def __init__(self):
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        
        welcome_message = f"""
🎉 ¡Hola {user.first_name}!

Bienvenido a **FideloBot** 🤖

Soy tu asistente de lealtad que te ayudará a:
• 🎯 Consultar tu balance de puntos
• 🎁 Recibir bonificaciones especiales
• 📊 Ver tu historial de actividad
• 🏪 Gestionar tu registro en negocios

Usa /help para ver todos los comandos disponibles.

¿En qué negocio quieres registrarte? 🏪
        """
        
        # Create inline keyboard with business options
        await self._show_business_selection(update, context, welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        help_text = """
📋 **Comandos disponibles:**

🏪 **Gestión de Negocios:**
• /businesses - Ver negocios disponibles
• /register - Registrarse en un negocio

👤 **Tu Cuenta:**
• /profile - Ver tu perfil
• /points - Ver tu balance de puntos
• /history - Ver historial de puntos

ℹ️ **Ayuda:**
• /help - Ver esta ayuda
• /start - Reiniciar el bot

¿Necesitas ayuda específica? ¡Pregúntame! 😊
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def businesses_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show available businesses."""
        await self._show_business_selection(update, context, "🏪 **Negocios disponibles:**")

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show businesses for registration."""
        await self._show_business_selection(update, context, "🏪 **Selecciona un negocio para registrarte:**")

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user profile information."""
        user = update.effective_user
        telegram_id = user.id
        
        try:
            # Find user's clients across all businesses
            clients = await sync_to_async(list)(
                Client.objects.filter(email=f"telegram_{telegram_id}@fidelo.local")
            )
            
            if not clients:
                await update.message.reply_text(
                    "🚫 No estás registrado en ningún negocio aún.\n"
                    "Usa /start para registrarte."
                )
                return
            
            message = f"👤 **Tu Perfil - {user.first_name}**\n\n"
            message += f"🆔 **Telegram ID:** {telegram_id}\n"
            message += f"👥 **Registrado en {len(clients)} negocio(s):**\n\n"
            
            for client in clients:
                try:
                    account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                    business_name = await sync_to_async(lambda: client.business.name)()
                    client_name = await sync_to_async(lambda: client.name)()
                    joined_at = await sync_to_async(lambda: client.joined_at.strftime('%d/%m/%Y'))()
                    message += f"🏪 **{business_name}**\n"
                    message += f"   📝 Nombre: {client_name}\n"
                    message += f"   💎 Puntos: {account.points_balance}\n"
                    message += f"   📅 Miembro desde: {joined_at}\n\n"
                except LoyaltyAccount.DoesNotExist:
                    business_name = await sync_to_async(lambda: client.business.name)()
                    client_name = await sync_to_async(lambda: client.name)()
                    joined_at = await sync_to_async(lambda: client.joined_at.strftime('%d/%m/%Y'))()
                    message += f"🏪 **{business_name}**\n"
                    message += f"   📝 Nombre: {client_name}\n"
                    message += f"   💎 Puntos: 0\n"
                    message += f"   📅 Miembro desde: {joined_at}\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await update.message.reply_text("❌ Error al consultar tu perfil.")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's points history."""
        user = update.effective_user
        telegram_id = user.id
        
        try:
            # Find user's clients across all businesses
            clients = await sync_to_async(list)(
                Client.objects.filter(email=f"telegram_{telegram_id}@fidelo.local")
            )
            
            if not clients:
                await update.message.reply_text(
                    "🚫 No estás registrado en ningún negocio aún.\n"
                    "Usa /start para registrarte."
                )
                return
            
            message = "📊 **Tu Historial de Puntos:**\n\n"
            has_transactions = False
            
            for client in clients:
                try:
                    # Get recent point events
                    from core.models import PointEvent
                    events = await sync_to_async(list)(
                        PointEvent.objects.filter(
                            client=client
                        ).order_by('-occurred_at')[:5]
                    )

                    if events:
                        has_transactions = True
                        business_name = await sync_to_async(lambda: client.business.name)()
                        message += f"🏪 **{business_name}**\n"
                        for event in events:
                            event_type = "➕" if event.points > 0 else "➖"
                            source_emoji = {
                                'purchase': '🛍️',
                                'birthday': '🎂',
                                'adjustment': '⚙️'
                            }.get(event.source, '📝')

                            message += f"   {event_type} {event.points} pts - {source_emoji} {event.get_source_display()}\n"
                            message += f"      📅 {event.occurred_at.strftime('%d/%m/%Y %H:%M')}\n"
                        message += "\n"
                        
                except Exception as e:
                    client_pk = await sync_to_async(lambda: client.pk)()
                    logger.error(f"Error getting transactions for client {client_pk}: {e}")
                    continue
            
            if not has_transactions:
                message += "📝 **No tienes transacciones aún.**\n\n"
                message += "Los puntos aparecerán aquí cuando:\n"
                message += "• Realices compras en los negocios\n"
                message += "• Recibas bonificaciones especiales\n"
                message += "• Sea tu cumpleaños 🎂"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing history: {e}")
            await update.message.reply_text("❌ Error al consultar tu historial.")

    async def _show_business_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
        """Helper method to show business selection inline keyboard."""
        try:
            # Use sync_to_async for database queries
            businesses = await sync_to_async(list)(
                Business.objects.filter(is_active=True)[:10]
            )
            
            if not businesses:
                await update.message.reply_text(
                    "🚫 No hay negocios disponibles en este momento.\n"
                    "Por favor, contacta al administrador."
                )
                return
            
            # Create inline keyboard with businesses
            keyboard = []
            for business in businesses:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🏪 {business.name}", 
                        callback_data=f"business_{business.business_id}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.message:
                await update.message.reply_text(
                    message, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text(
                    message, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error showing business selection: {e}")
            error_message = "❌ Error al cargar los negocios. Intenta de nuevo más tarde."
            
            if update.message:
                await update.message.reply_text(error_message)
            else:
                await update.callback_query.edit_message_text(error_message)

    async def handle_business_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle business selection from inline keyboard."""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extract business_id from callback data
            callback_data = query.data
            if not callback_data.startswith('business_'):
                return
                
            business_id = callback_data.replace('business_', '')
            business = await sync_to_async(Business.objects.get)(business_id=business_id)
            
            user = update.effective_user
            telegram_id = user.id
            
            # Check if user is already registered with this business
            try:
                client = await sync_to_async(Client.objects.get)(
                    business=business,
                    email=f"telegram_{telegram_id}@fidelo.local"  # Temporary email format
                )
                
                account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                
                message = f"""
✅ **Ya estás registrado en {business.name}!**

👤 **Tu información:**
• Cliente: {client.name}
• Puntos actuales: **{account.points_balance}** pts
• Miembro desde: {client.joined_at}

¿Qué quieres hacer ahora?
                """
                
                keyboard = [
                    [InlineKeyboardButton("🎯 Ver Puntos", callback_data=f"points_{business.business_id}")],
                    [InlineKeyboardButton("📊 Historial", callback_data=f"history_{business.business_id}")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Client.DoesNotExist:
                # User not registered, start registration process
                message = f"""
🏪 **{business.name}**

¡Perfecto! Te registraremos en este negocio.

📝 **Información del programa:**
• {business.points_per_currency} puntos por cada peso gastado
• {business.birthday_bonus_points} puntos de regalo en tu cumpleaños

Para completar tu registro, necesito algunos datos. Comenzemos:

📱 **Número de teléfono** (formato internacional):
Ejemplo: +5212345678901
                """

                # Store business_id in user context
                context.user_data['registering_business_id'] = str(business.business_id)
                context.user_data['registration_step'] = 'awaiting_phone'

                await query.edit_message_text(message, parse_mode='Markdown')
                
        except Business.DoesNotExist:
            await query.edit_message_text("❌ Negocio no encontrado.")
        except Exception as e:
            logger.error(f"Error handling business selection: {e}")
            await query.edit_message_text("❌ Error procesando tu selección. Intenta de nuevo.")

    async def handle_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user registration process with complete data collection."""
        if 'registration_step' not in context.user_data:
            return

        user = update.effective_user
        telegram_id = user.id
        message_text = update.message.text.strip()

        try:
            step = context.user_data['registration_step']

            if step == 'awaiting_phone':
                # First step: phone number
                if not self._validate_phone(message_text):
                    await update.message.reply_text(
                        "❌ **Formato de teléfono inválido**\n\n"
                        "Por favor ingresa tu teléfono con formato internacional:\n"
                        "Ejemplo: +5212345678901\n\n"
                        "📱 Ingresa tu número de teléfono:"
                    )
                    return

                # Check if phone already exists
                business_id = context.user_data['registering_business_id']
                business = await sync_to_async(Business.objects.get)(business_id=business_id)

                # DEBUG: Log search details
                logger.info(f"DEBUG: Searching for phone '{message_text}' in business '{business.name}' (ID: {business.business_id})")

                try:
                    existing_client = await sync_to_async(Client.objects.get)(
                        business=business, phone=message_text
                    )
                    logger.info(f"DEBUG: FOUND client '{existing_client.name}' with phone '{existing_client.phone}'")

                    # Phone exists - update with Telegram info and fill missing data
                    context.user_data['existing_client_id'] = str(existing_client.client_id)
                    context.user_data['client_phone'] = message_text

                    missing_data = []
                    if not existing_client.name or existing_client.name.startswith('Cliente '):
                        missing_data.append('nombre completo')
                    if not existing_client.email or existing_client.email.startswith('phone_'):
                        missing_data.append('email')
                    if not existing_client.birthday:
                        missing_data.append('fecha de nacimiento')

                    if missing_data:
                        missing_str = ', '.join(missing_data)

                        # Show existing purchases even with missing data
                        purchase_info = await self._get_client_purchase_summary(existing_client)

                        await update.message.reply_text(
                            f"✅ **¡Teléfono encontrado!**\n\n"
                            f"Ya tienes una cuenta en **{business.name}**, pero necesitamos completar algunos datos:\n\n"
                            f"📝 Datos faltantes: {missing_str}\n\n"
                            f"{purchase_info}\n"
                            f"👤 **Nombre completo:**"
                        )
                        context.user_data['registration_step'] = 'awaiting_name'
                    else:
                        # Link Telegram to existing complete account
                        existing_client.email = f"telegram_{telegram_id}@fidelo.local"
                        await sync_to_async(existing_client.save)()

                        await self._show_registration_success_with_history(update, context, business, existing_client, is_update=True)
                        return

                except Client.DoesNotExist:
                    # New phone - continue with registration
                    logger.info(f"DEBUG: CLIENT NOT FOUND with phone '{message_text}' in business '{business.name}' (ID: {business.business_id})")
                    context.user_data['client_phone'] = message_text
                    await update.message.reply_text(
                        "📱 **Nuevo número registrado**\n\n"
                        "👤 **Nombre completo:**"
                    )
                    context.user_data['registration_step'] = 'awaiting_name'

            elif step == 'awaiting_name':
                if len(message_text) < 2:
                    await update.message.reply_text(
                        "❌ **Nombre muy corto**\n\n"
                        "👤 **Ingresa tu nombre completo:**"
                    )
                    return

                context.user_data['client_name'] = message_text
                await self._complete_registration(update, context)

            elif step == 'awaiting_email':
                if message_text.lower() == '/skip':
                    context.user_data['client_email'] = ''
                elif '@' not in message_text:
                    await update.message.reply_text(
                        "❌ **Email inválido**\n\n"
                        "📧 **Ingresa un email válido** o presiona /skip para omitir:"
                    )
                    return
                else:
                    context.user_data['client_email'] = message_text

                await update.message.reply_text(
                    "🎂 **Fecha de nacimiento** (opcional - presiona /skip para omitir)\n\n"
                    "Formato: DD/MM/AAAA\n"
                    "Ejemplo: 15/05/1990"
                )
                context.user_data['registration_step'] = 'awaiting_birthday'

            elif step == 'awaiting_birthday':
                birthday = None
                if message_text.lower() != '/skip':
                    birthday = self._parse_birthday(message_text)
                    if not birthday:
                        await update.message.reply_text(
                            "❌ **Fecha inválida**\n\n"
                            "🎂 **Formato correcto:** DD/MM/AAAA\n"
                            "Ejemplo: 15/05/1990\n\n"
                            "O presiona /skip para omitir:"
                        )
                        return

                context.user_data['client_birthday'] = birthday
                await self._complete_registration(update, context)

        except Business.DoesNotExist:
            await update.message.reply_text("❌ Error: Negocio no encontrado.")
        except Exception as e:
            logger.error(f"Error in registration: {e}")
            await update.message.reply_text(
                "❌ Error en el registro. Por favor intenta de nuevo con /start"
            )

    async def points_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's points balance."""
        user = update.effective_user
        telegram_id = user.id
        
        try:
            # Find user's clients across all businesses
            clients = await sync_to_async(list)(
                Client.objects.filter(email=f"telegram_{telegram_id}@fidelo.local")
            )
            
            if not clients:
                await update.message.reply_text(
                    "🚫 No estás registrado en ningún negocio aún.\n"
                    "Usa /start para registrarte."
                )
                return
            
            message = "🎯 **Tus puntos:**\n\n"
            
            for client in clients:
                try:
                    account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                    business_name = await sync_to_async(lambda: client.business.name)()
                    message += f"🏪 **{business_name}**\n"
                    message += f"   💎 {account.points_balance} puntos\n\n"
                except LoyaltyAccount.DoesNotExist:
                    business_name = await sync_to_async(lambda: client.business.name)()
                    message += f"🏪 **{business_name}**\n"
                    message += f"   💎 0 puntos\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing points: {e}")
            await update.message.reply_text("❌ Error al consultar tus puntos.")

    async def handle_help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle help callback from inline button."""
        query = update.callback_query
        await query.answer()
        
        help_text = """
📋 **Comandos disponibles:**

🏪 **Gestión de Negocios:**
• /businesses - Ver negocios disponibles
• /register - Registrarse en un negocio

👤 **Tu Cuenta:**
• /profile - Ver tu perfil
• /points - Ver tu balance de puntos
• /history - Ver historial de puntos

ℹ️ **Ayuda:**
• /help - Ver esta ayuda
• /start - Reiniciar el bot

¿Necesitas ayuda específica? ¡Pregúntame! 😊
        """
        
        await query.edit_message_text(help_text, parse_mode='Markdown')

    async def handle_points_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle points callback from inline button."""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extract business_id from callback data
            callback_data = query.data
            if not callback_data.startswith('points_'):
                return
                
            business_id = callback_data.replace('points_', '')
            business = await sync_to_async(Business.objects.get)(business_id=business_id)
            
            user = update.effective_user
            telegram_id = user.id
            
            # Find user's client for this business
            try:
                client = await sync_to_async(Client.objects.get)(
                    business=business,
                    email=f"telegram_{telegram_id}@fidelo.local"
                )
                
                try:
                    account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                    points_balance = account.points_balance
                except LoyaltyAccount.DoesNotExist:
                    points_balance = 0
                
                if points_balance > 0:
                    message = f"""
🎯 **Tus puntos en {business.name}**

💎 **Balance actual:** {points_balance} puntos

📊 **Información:**
• Ganancia por compra: {business.points_per_currency} pts por peso
• Bonus cumpleaños: {business.birthday_bonus_points} pts

🚀 ¡Sigue comprando para acumular más puntos!
                    """
                else:
                    message = f"""
🎯 **Tus puntos en {business.name}**

💎 **Balance actual:** 0 puntos

😊 **¡Aún no tienes puntos!**

📝 **Para ganar puntos:**
• El negocio registrará tus compras automáticamente
• Ganas {business.points_per_currency} puntos por cada peso gastado
• Recibe {business.birthday_bonus_points} puntos de regalo en tu cumpleaños

💰 ¡Haz tu primera compra en el negocio para empezar a acumular!
                    """
                
                keyboard = [
                    [InlineKeyboardButton("🏪 Ver Negocios", callback_data="businesses")],
                    [InlineKeyboardButton("📊 Ver Historial", callback_data=f"history_{business.business_id}")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Client.DoesNotExist:
                await query.edit_message_text(
                    "❌ No estás registrado en este negocio.\n"
                    "Usa /start para registrarte."
                )
                
        except Business.DoesNotExist:
            await query.edit_message_text("❌ Negocio no encontrado.")
        except Exception as e:
            logger.error(f"Error handling points callback: {e}")
            await query.edit_message_text("❌ Error al consultar tus puntos.")

    async def handle_businesses_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle businesses callback from inline button."""
        query = update.callback_query
        await query.answer()
        
        await self._show_business_selection(update, context, "🏪 **Negocios disponibles:**")

    async def handle_history_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle history callback from inline button."""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extract business_id from callback data
            callback_data = query.data
            if not callback_data.startswith('history_'):
                return
                
            business_id = callback_data.replace('history_', '')
            business = await sync_to_async(Business.objects.get)(business_id=business_id)
            
            user = update.effective_user
            telegram_id = user.id
            
            # Find user's client for this business
            try:
                client = await sync_to_async(Client.objects.get)(
                    business=business,
                    email=f"telegram_{telegram_id}@fidelo.local"
                )
                
                # Get recent point events
                from core.models import PointEvent
                events = await sync_to_async(list)(
                    PointEvent.objects.filter(
                        client=client
                    ).order_by('-occurred_at')[:10]
                )
                
                message = f"📊 **Historial de {business.name}**\n\n"

                if events:
                    for event in events:
                        event_type = "➕" if event.points > 0 else "➖"
                        source_emoji = {
                            'purchase': '🛍️',
                            'birthday': '🎂',
                            'adjustment': '⚙️'
                        }.get(event.source, '📝')

                        message += f"{event_type} **{event.points} pts** - {source_emoji} {event.get_source_display()}\n"
                        if event.note:
                            message += f"   📝 {event.note}\n"
                        message += f"   📅 {event.occurred_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                else:
                    message += "📝 **No tienes eventos de puntos en este negocio aún.**\n\n"
                    message += "Los puntos aparecerán aquí cuando:\n"
                    message += "• Realices compras en el negocio\n"
                    message += "• Recibas bonificaciones especiales\n"
                    message += "• Sea tu cumpleaños 🎂"
                
                keyboard = [
                    [InlineKeyboardButton("🎯 Ver Puntos", callback_data=f"points_{business.business_id}")],
                    [InlineKeyboardButton("🏪 Ver Negocios", callback_data="businesses")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Client.DoesNotExist:
                await query.edit_message_text(
                    "❌ No estás registrado en este negocio.\n"
                    "Usa /start para registrarte."
                )
                
        except Business.DoesNotExist:
            await query.edit_message_text("❌ Negocio no encontrado.")
        except Exception as e:
            logger.error(f"Error handling history callback: {e}")
            await query.edit_message_text("❌ Error al consultar tu historial.")

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle unknown commands."""
        if 'registration_step' in context.user_data:
            # User is in registration process
            await self.handle_registration(update, context)
        else:
            await update.message.reply_text(
                "🤔 No entiendo ese comando.\n"
                "Usa /help para ver los comandos disponibles."
            )

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        import re
        # Basic validation for international format
        pattern = r'^\+\d{10,15}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

    def _parse_birthday(self, date_str: str):
        """Parse birthday string to date object."""
        from datetime import datetime
        try:
            # Try DD/MM/YYYY format
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                # Try DD-MM-YYYY format
                return datetime.strptime(date_str, '%d-%m-%Y').date()
            except ValueError:
                return None

    async def _complete_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete the registration process."""
        try:
            user = update.effective_user
            telegram_id = user.id
            business_id = context.user_data['registering_business_id']
            business = await sync_to_async(Business.objects.get)(business_id=business_id)

            client_data = {
                'business': business,
                'name': context.user_data['client_name'],
                'phone': context.user_data['client_phone'],
                'birthday': context.user_data.get('client_birthday'),
                'email': f"telegram_{telegram_id}@fidelo.local"
            }

            # Handle email
            if context.user_data.get('client_email'):
                # If user provided email, use it but keep telegram format as backup
                real_email = context.user_data['client_email']
                client_data['email'] = f"telegram_{telegram_id}@fidelo.local"  # Keep for system
                # We'll store the real email in a separate field if needed

            # Check if updating existing client
            if 'existing_client_id' in context.user_data:
                # Update existing client
                client_id = context.user_data['existing_client_id']
                client = await sync_to_async(Client.objects.get)(client_id=client_id)

                # Update fields
                client.name = client_data['name']
                client.email = client_data['email']
                if client_data['birthday']:
                    client.birthday = client_data['birthday']

                await sync_to_async(client.save)()
                is_update = True
            else:
                # Create new client
                client = await sync_to_async(ClientService.create_client_with_account)(**client_data)
                is_update = False

            await self._show_registration_success(update, context, business, client, is_update)

        except Exception as e:
            logger.error(f"Error completing registration: {e}")
            await update.message.reply_text(
                "❌ Error completando el registro. Intenta de nuevo con /start"
            )

    async def _show_registration_success(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       business, client, is_update: bool = False):
        """Show registration success message."""
        try:
            # Clear registration data
            context.user_data.clear()

            if is_update:
                success_message = f"""
🎉 **¡Cuenta vinculada exitosamente!**

Tu teléfono ha sido vinculado a tu cuenta de Telegram en **{business.name}**.

👤 **Tu información:**
• Nombre: {client.name}
• Teléfono: {client.phone}
• Cuenta vinculada a Telegram

🎯 **Tu cuenta:**
                """
            else:
                success_message = f"""
🎉 **¡Registro completado!**

Bienvenido a **{business.name}**, {client.name}!

👤 **Tu información:**
• Nombre: {client.name}
• Teléfono: {client.phone}
• Email: {client.email if not client.email.startswith('telegram_') else 'Email de Telegram'}

🎯 **Tu cuenta:**
                """

            try:
                account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                points_balance = account.points_balance
            except LoyaltyAccount.DoesNotExist:
                points_balance = 0

            success_message += f"""
• Puntos actuales: **{points_balance}** pts
• Ganancia por compra: {business.points_per_currency} pts por peso
• Bonus cumpleaños: {business.birthday_bonus_points} pts

🚀 **¡Ya puedes empezar a acumular puntos!**

¿Qué quieres hacer ahora?
            """

            keyboard = [
                [InlineKeyboardButton("🎯 Ver Mis Puntos", callback_data=f"points_{business.business_id}")],
                [InlineKeyboardButton("📊 Ver Historial Completo", callback_data=f"history_{business.business_id}")],
                [InlineKeyboardButton("📋 Ver Comandos", callback_data="help")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                success_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error showing registration success: {e}")
            await update.message.reply_text(
                "✅ Registro completado exitosamente!\n"
                "Usa /help para ver los comandos disponibles."
            )

    def setup_handlers(self):
        """Set up bot command handlers."""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("businesses", self.businesses_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("points", points_command))
        self.application.add_handler(CommandHandler("history", self.history_command))

        # Advanced features
        self.application.add_handler(CommandHandler("link_telegram", link_telegram_command))
        self.application.add_handler(CommandHandler("notifications", notifications_command))
        self.application.add_handler(CommandHandler("admin_points", admin_send_points))

        # Remove any existing purchase handler if it exists
        # No purchase command should be available for users
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(
            self.handle_business_selection, 
            pattern=r'^business_'
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_help_callback, 
            pattern=r'^help$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_points_callback, 
            pattern=r'^points_'
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_businesses_callback, 
            pattern=r'^businesses$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_history_callback,
            pattern=r'^history_'
        ))

        # Advanced callbacks
        self.application.add_handler(CallbackQueryHandler(
            handle_link_callback,
            pattern=r'^link_'
        ))
        self.application.add_handler(CallbackQueryHandler(
            loyalty_programs_callback,
            pattern=r'^loyalty_programs$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            update_profile_callback,
            pattern=r'^update_'
        ))
        self.application.add_handler(CallbackQueryHandler(
            test_notification_callback,
            pattern=r'^test_notification$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            show_history_callback,
            pattern=r'^show_history$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            back_to_points_callback,
            pattern=r'^back_to_points$'
        ))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.unknown_command
        ))

    def get_application(self):
        """Get or create the Telegram application."""
        if not self.application:
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            self.setup_handlers()
        
        return self.application


    async def _get_client_purchase_summary(self, client):
        """Get a summary of client's existing purchases."""
        try:
            # Get recent purchases
            purchases = await sync_to_async(list)(
                Purchase.objects.filter(client=client).order_by('-purchased_at')[:3]
            )

            if not purchases:
                return "📝 **Historial:** Sin compras registradas aún"

            # Get account info
            try:
                account = await sync_to_async(LoyaltyAccount.objects.get)(client=client)
                points_balance = account.points_balance
            except LoyaltyAccount.DoesNotExist:
                points_balance = 0

            summary = f"💎 **Puntos actuales:** {points_balance} pts\n\n"
            summary += "🛍️ **Últimas compras:**\n"

            for purchase in purchases:
                purchase_date = purchase.purchased_at.strftime('%d/%m/%Y')
                points_earned = int(purchase.amount * purchase.business.points_per_currency)
                summary += f"• ${purchase.amount} {purchase.currency} - {points_earned} pts ({purchase_date})\n"

            return summary

        except Exception as e:
            logger.error(f"Error getting purchase summary: {e}")
            return "📝 **Historial:** Error al cargar compras"

    async def _show_registration_success_with_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                                    business, client, is_update: bool = False):
        """Show registration success message with purchase history."""
        try:
            # Clear registration data
            context.user_data.clear()

            # Get purchase history
            purchase_info = await self._get_client_purchase_summary(client)

            success_message = f"""
🎉 **¡Cuenta vinculada exitosamente!**

Tu teléfono ha sido vinculado a tu cuenta de Telegram en **{business.name}**.

👤 **Tu información:**
• Nombre: {client.name}
• Teléfono: {client.phone}
• Cuenta vinculada a Telegram

{purchase_info}

🚀 **¡Ya puedes ver todas tus compras y puntos!**

¿Qué quieres hacer ahora?
            """

            keyboard = [
                [InlineKeyboardButton("🎯 Ver Mis Puntos", callback_data=f"points_{business.business_id}")],
                [InlineKeyboardButton("📊 Ver Historial Completo", callback_data=f"history_{business.business_id}")],
                [InlineKeyboardButton("📋 Ver Comandos", callback_data="help")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                success_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error showing registration success with history: {e}")
            await update.message.reply_text(
                "✅ Registro completado exitosamente!\n"
                "Usa /help para ver los comandos disponibles."
            )


# Global bot instance
bot_instance = FideloBot()