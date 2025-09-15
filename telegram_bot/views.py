import json
import asyncio
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from telegram import Update
from .bot import bot_instance

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """Handle Telegram webhook requests."""
    
    def post(self, request):
        """Process incoming Telegram updates."""
        try:
            # Parse JSON data
            json_data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Received webhook data: {json_data}")
            
            # Create Telegram Update object
            application = bot_instance.get_application()
            update = Update.de_json(json_data, application.bot)
            
            # Process the update asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(update))
            loop.close()
            
            return HttpResponse("OK")
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["GET"])
def webhook_info(request):
    """Get webhook information (for debugging)."""
    try:
        application = bot_instance.get_application()
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        webhook_info = loop.run_until_complete(application.bot.get_webhook_info())
        loop.close()
        
        info = {
            'webhook_url': webhook_info.url,
            'has_custom_certificate': webhook_info.has_custom_certificate,
            'pending_update_count': webhook_info.pending_update_count,
            'last_error_date': webhook_info.last_error_date,
            'last_error_message': webhook_info.last_error_message,
            'max_connections': webhook_info.max_connections,
            'allowed_updates': webhook_info.allowed_updates,
        }
        
        return HttpResponse(json.dumps(info, indent=2, default=str), content_type='application/json')
        
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
@csrf_exempt
def set_webhook(request):
    """Set Telegram webhook URL."""
    try:
        from django.conf import settings
        
        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        if not webhook_url:
            return HttpResponseBadRequest("TELEGRAM_WEBHOOK_URL not configured")
        
        application = bot_instance.get_application()
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(application.bot.set_webhook(webhook_url))
        loop.close()
        
        if result:
            return HttpResponse(f"Webhook set successfully to: {webhook_url}")
        else:
            return HttpResponseBadRequest("Failed to set webhook")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["POST"])
@csrf_exempt
def delete_webhook(request):
    """Delete Telegram webhook."""
    try:
        application = bot_instance.get_application()
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(application.bot.delete_webhook())
        loop.close()
        
        if result:
            return HttpResponse("Webhook deleted successfully")
        else:
            return HttpResponseBadRequest("Failed to delete webhook")
            
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return HttpResponseBadRequest(f"Error: {str(e)}")


@require_http_methods(["GET"])
def bot_info(request):
    """Get bot information."""
    try:
        application = bot_instance.get_application()
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        me = loop.run_until_complete(application.bot.get_me())
        loop.close()
        
        info = {
            'bot_id': me.id,
            'bot_username': me.username,
            'bot_first_name': me.first_name,
            'bot_can_join_groups': me.can_join_groups,
            'bot_can_read_all_group_messages': me.can_read_all_group_messages,
            'bot_supports_inline_queries': me.supports_inline_queries,
        }
        
        return HttpResponse(json.dumps(info, indent=2), content_type='application/json')
        
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        return HttpResponseBadRequest(f"Error: {str(e)}")