import asyncio
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram_bot.bot import bot_instance


class Command(BaseCommand):
    help = 'Run the Telegram bot in polling mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook',
            action='store_true',
            help='Set up webhook instead of polling',
        )

    def handle(self, *args, **options):
        # Configure logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        logger = logging.getLogger(__name__)
        
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_BOT_TOKEN not configured in settings')
            )
            return

        try:
            application = bot_instance.get_application()
            
            if options['webhook']:
                # Set up webhook
                self.setup_webhook(application, logger)
            else:
                # Run in polling mode
                self.run_polling(application, logger)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def setup_webhook(self, application, logger):
        """Set up webhook for the bot."""
        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        if not webhook_url:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_WEBHOOK_URL not configured in settings')
            )
            return

        async def set_webhook():
            result = await application.bot.set_webhook(webhook_url)
            if result:
                logger.info(f"Webhook set successfully to: {webhook_url}")
                self.stdout.write(
                    self.style.SUCCESS(f'Webhook set to: {webhook_url}')
                )
            else:
                logger.error("Failed to set webhook")
                self.stdout.write(self.style.ERROR('Failed to set webhook'))

        # Run the async function
        asyncio.run(set_webhook())

    def run_polling(self, application, logger):
        """Run bot in polling mode."""
        logger.info("Starting bot in polling mode...")
        self.stdout.write(self.style.SUCCESS('Starting FideloBot in polling mode...'))
        self.stdout.write('Press Ctrl+C to stop')
        
        # Run the bot with polling
        application.run_polling(
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=-1,
            read_timeout=2,
            write_timeout=2,
            connect_timeout=2,
            pool_timeout=2
        )