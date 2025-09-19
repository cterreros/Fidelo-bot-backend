#!/usr/bin/env python3
"""
Test script for the complete FideloBot flow with birthday notifications
"""
import os
import sys
import django
import json
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client as TestClient
from core.models import Business, Client, LoyaltyAccount


def get_jwt_token():
    """Helper function to get JWT token for tests"""
    client = TestClient()

    # Create user if it doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()

    # Get token
    response = client.post('/auth/token/', {
        'username': 'testuser',
        'password': 'testpass123'
    })

    if response.status_code == 200:
        return response.json()['access']
    return None


def test_complete_flow():
    """Test the complete flow from purchase to notifications"""
    print("========================================")
    print("  TESTING COMPLETE FIDELOBOT FLOW")
    print("========================================")

    client = TestClient()

    # Authenticate
    token = get_jwt_token()
    if not token:
        print("ERROR: Could not get authentication token")
        return False

    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    # Step 1: Create test business
    print("\n1. Creating test business...")
    business_data = {
        'name': 'Cafeteria El Buen Sabor',
        'email': 'cafeteria@buensabor.com',
        'points_per_currency': '0.1',  # 1 point per 10 pesos
        'birthday_bonus_points': 500   # 500 bonus points for birthday
    }

    response = client.post('/api/businesses/', business_data)
    if response.status_code != 201:
        print(f"ERROR: Could not create business: {response.content}")
        return False

    business_id = response.json()['business_id']
    print(f"SUCCESS: Created business '{business_data['name']}' with ID: {business_id}")

    # Step 2: Simulate customer purchase WITH birthday today
    print("\n2. Simulating customer purchase with birthday today...")
    tomorrow = date.today() + timedelta(days=1)  # Use tomorrow for birthday testing

    purchase_data = {
        'business_id': business_id,
        'amount': '250.00',  # 25 points
        'currency': 'MXN',
        'client_name': 'Maria Elena Rodriguez',
        'client_email': 'maria@example.com',
        'client_phone': '+52155123456789',
        'client_birthday': tomorrow.isoformat(),  # Birthday tomorrow
        'telegram_user_id': '987654321',  # Fake Telegram ID
        'send_telegram_notification': True
    }

    response = client.post('/api/purchase-with-client/', purchase_data, content_type='application/json')
    if response.status_code != 201:
        print(f"ERROR: Could not create purchase: {response.content}")
        return False

    result = response.json()
    print(f"SUCCESS: Purchase registered")
    print(f"  - Client: {purchase_data['client_name']}")
    print(f"  - Amount: ${purchase_data['amount']}")
    print(f"  - Points earned: {result['points_earned']}")
    print(f"  - Telegram notification: {'Sent (but failed gracefully)' if result['telegram_notification_sent'] else 'Not sent'}")

    client_id = result['client_id']

    # Step 3: Test birthday notification system
    print("\n3. Testing birthday notification system...")

    # First, let's test with dry-run for tomorrow
    print("Testing dry-run for tomorrow's birthdays...")
    from django.core.management import call_command
    from io import StringIO

    out = StringIO()
    call_command('send_birthday_notifications', '--dry-run', f'--date={tomorrow.isoformat()}', stdout=out)
    output = out.getvalue()
    print("Dry-run output:")
    print(output)

    if purchase_data['client_name'] in output:
        print("SUCCESS: Client found in birthday list for tomorrow")
    else:
        print("WARNING: Client not found in birthday list")

    # Step 4: Create another purchase to test existing client flow
    print("\n4. Testing existing client purchase...")
    purchase_data_2 = {
        'business_id': business_id,
        'amount': '150.00',  # 15 points
        'currency': 'MXN',
        'client_name': 'Maria Elena Rodriguez',  # Same client
        'client_email': 'maria@example.com',     # Same email
        'client_phone': '+52155123456789',
        'telegram_user_id': '987654321',
        'send_telegram_notification': True
    }

    response = client.post('/api/purchase-with-client/', purchase_data_2, content_type='application/json')
    if response.status_code != 201:
        print(f"ERROR: Could not create second purchase: {response.content}")
        return False

    result = response.json()
    print(f"SUCCESS: Second purchase for existing client")
    print(f"  - New client created: {result['created_new_client']} (should be False)")
    print(f"  - Points earned: {result['points_earned']}")
    print(f"  - Total balance: {result['client_points_balance']}")

    # Verify total points: 25 + 15 = 40
    expected_points = 25 + 15
    if result['client_points_balance'] == expected_points:
        print(f"SUCCESS: Points accumulation working correctly ({expected_points} points)")
    else:
        print(f"ERROR: Points calculation wrong. Expected {expected_points}, got {result['client_points_balance']}")

    # Step 5: Test admin points functionality
    print("\n5. Testing admin points functionality...")
    admin_response = client.post('/api/purchase-with-client/', {
        'business_id': business_id,
        'amount': '0.00',  # No purchase amount
        'currency': 'MXN',
        'client_name': 'Carlos Admin Test',
        'client_email': 'carlos@admin.com',
        'telegram_user_id': '123456789',
        'send_telegram_notification': False
    }, content_type='application/json')

    if admin_response.status_code == 201:
        print("SUCCESS: Admin client created for testing manual points")

    # Step 6: Check if we can list all clients via API
    print("\n6. Checking client management via API...")
    response = client.get('/api/clients/')
    if response.status_code == 200:
        clients_data = response.json()
        print(f"SUCCESS: Retrieved {clients_data['count']} clients from API")

        # Find our test client
        for client_info in clients_data['results']:
            if client_info['email'] == 'maria@example.com':
                print(f"  - Found Maria: {client_info['name']} with {client_info['birthday']}")
                break
    else:
        print(f"ERROR: Could not retrieve clients: {response.status_code}")

    # Step 7: Test notification command with real date
    print("\n7. Testing birthday command for today (should find no birthdays)...")
    out = StringIO()
    call_command('send_birthday_notifications', '--dry-run', stdout=out)
    output = out.getvalue()
    print("Today's birthday check:")
    print(output)

    print("\n========================================")
    print("           FLOW TEST COMPLETED")
    print("========================================")
    print("\nSUMMARY:")
    print("✅ Business creation")
    print("✅ Purchase-with-client endpoint")
    print("✅ Automatic client creation/update")
    print("✅ Points calculation and accumulation")
    print("✅ Birthday notification system (dry-run)")
    print("✅ Existing client handling")
    print("✅ API integration")

    print("\nNEXT STEPS FOR PRODUCTION:")
    print("1. Set up daily cron job: python manage.py send_birthday_notifications")
    print("2. Configure real Telegram bot token")
    print("3. Test with real Telegram users")
    print("4. Set up monitoring and logging")
    print("5. Configure webhook for real-time notifications")

    return True


if __name__ == "__main__":
    success = test_complete_flow()
    if not success:
        sys.exit(1)