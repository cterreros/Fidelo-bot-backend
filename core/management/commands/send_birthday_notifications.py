"""
Django management command to send birthday notifications
This command should be run daily via cron job or task scheduler
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from core.telegram_notifications import check_and_send_birthday_notifications


class Command(BaseCommand):
    help = 'Send birthday notifications to clients whose birthday is today'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending notifications'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Check for specific date (YYYY-MM-DD format) instead of today'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f"Starting birthday notifications check at {timezone.now()}")
        )

        try:
            if options['dry_run']:
                self.stdout.write("DRY RUN MODE - No notifications will be sent")

            if options['date']:
                # Parse custom date
                try:
                    check_date = date.fromisoformat(options['date'])
                    self.stdout.write(f"Checking for birthdays on: {check_date}")
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR("Invalid date format. Use YYYY-MM-DD")
                    )
                    return
            else:
                check_date = date.today()
                self.stdout.write(f"Checking for birthdays today: {check_date}")

            # Get clients with birthdays
            from core.models import Client
            birthday_clients = Client.objects.filter(
                birthday__month=check_date.month,
                birthday__day=check_date.day
            ).select_related('business')

            self.stdout.write(f"Found {birthday_clients.count()} clients with birthdays")

            if options['dry_run']:
                for client in birthday_clients:
                    self.stdout.write(
                        f"  - {client.name} ({client.email}) at {client.business.name}"
                    )
                self.stdout.write("DRY RUN COMPLETE - No notifications sent")
                return

            # Send actual notifications
            notifications_sent = check_and_send_birthday_notifications()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Birthday notification process completed. "
                    f"Notifications sent: {notifications_sent}"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during birthday notifications: {str(e)}")
            )
            raise