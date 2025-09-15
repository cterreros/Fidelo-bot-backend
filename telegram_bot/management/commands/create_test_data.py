from django.core.management.base import BaseCommand
from core.models import Business
from core.services import ClientService


class Command(BaseCommand):
    help = 'Create test data for bot development'

    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")
        
        # Create test businesses
        businesses_data = [
            {
                'name': 'Café Luna',
                'email': 'cafe@luna.com',
                'points_per_currency': 0.1,  # 1 punto por cada $10
                'birthday_bonus_points': 50,
            },
            {
                'name': 'Panadería Sol',
                'email': 'panaderia@sol.com', 
                'points_per_currency': 0.05,  # 1 punto por cada $20
                'birthday_bonus_points': 100,
            },
            {
                'name': 'Tienda Verde',
                'email': 'tienda@verde.com',
                'points_per_currency': 0.2,  # 1 punto por cada $5
                'birthday_bonus_points': 75,
            }
        ]
        
        for business_data in businesses_data:
            business, created = Business.objects.get_or_create(
                email=business_data['email'],
                defaults=business_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created business: {business.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Business already exists: {business.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\nTest data creation completed!')
        )
        self.stdout.write(
            '\nYou can now test the bot with these businesses:'
        )
        
        for business in Business.objects.filter(is_active=True):
            self.stdout.write(f"  - {business.name} - {business.points_per_currency} pts/$")
        
        self.stdout.write(
            f'\nRun bot with: python manage.py run_bot'
        )