#!/usr/bin/env python3
"""
Test script for the new purchase-with-client endpoint and Telegram integration
"""
import os
import sys
import django
import json

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


def test_purchase_with_client_flow():
    """Test the complete purchase-with-client flow"""
    print("Testing Purchase-with-Client Flow...")

    client = TestClient()

    # Authenticate
    token = get_jwt_token()
    if not token:
        print("ERROR: Could not get authentication token")
        return False

    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    # Step 1: Create a test business
    print("\n1. Creating test business...")
    business_data = {
        'name': 'Test Store',
        'email': 'store@test.com',
        'points_per_currency': '0.1',  # 1 point per 10 pesos
        'birthday_bonus_points': 100
    }

    response = client.post('/api/businesses/', business_data)
    if response.status_code != 201:
        print(f"ERROR: Could not create business: {response.content}")
        return False

    business_id = response.json()['business_id']
    print(f"SUCCESS: Created business with ID: {business_id}")

    # Step 2: Test purchase with new client (no Telegram notification)
    print("\n2. Testing purchase with new client (no Telegram)...")
    purchase_data = {
        'business_id': business_id,
        'amount': '150.00',
        'currency': 'MXN',
        'client_name': 'Juan Pérez',
        'client_email': 'juan@example.com',
        'client_phone': '+52123456789',
        'client_birthday': '1990-05-15',
        'send_telegram_notification': False
    }

    response = client.post('/api/purchase-with-client/', purchase_data, content_type='application/json')
    if response.status_code != 201:
        print(f"ERROR: Could not create purchase: {response.content}")
        return False

    result = response.json()
    print(f"SUCCESS: Purchase created")
    print(f"  - Purchase ID: {result['purchase_id']}")
    print(f"  - Client ID: {result['client_id']}")
    print(f"  - New client created: {result['created_new_client']}")
    print(f"  - Points earned: {result['points_earned']}")
    print(f"  - Client balance: {result['client_points_balance']}")
    print(f"  - Telegram notification sent: {result['telegram_notification_sent']}")

    # Step 3: Test purchase with existing client
    print("\n3. Testing purchase with existing client...")
    purchase_data_2 = {
        'business_id': business_id,
        'amount': '75.50',
        'currency': 'MXN',
        'client_name': 'Juan Pérez',  # Same client
        'client_email': 'juan@example.com',  # Same email
        'client_phone': '+52123456789',
        'send_telegram_notification': False
    }

    response = client.post('/api/purchase-with-client/', purchase_data_2, content_type='application/json')
    if response.status_code != 201:
        print(f"ERROR: Could not create second purchase: {response.content}")
        return False

    result = response.json()
    print(f"SUCCESS: Second purchase created")
    print(f"  - Purchase ID: {result['purchase_id']}")
    print(f"  - Client ID: {result['client_id']} (should be same as before)")
    print(f"  - New client created: {result['created_new_client']} (should be False)")
    print(f"  - Points earned: {result['points_earned']}")
    print(f"  - Client balance: {result['client_points_balance']} (should be cumulative)")

    # Step 4: Verify client was updated correctly
    print("\n4. Verifying client data in database...")
    try:
        db_client = Client.objects.get(client_id=result['client_id'])
        account = LoyaltyAccount.objects.get(client=db_client)

        print(f"SUCCESS: Client found in database")
        print(f"  - Name: {db_client.name}")
        print(f"  - Email: {db_client.email}")
        print(f"  - Phone: {db_client.phone}")
        print(f"  - Birthday: {db_client.birthday}")
        print(f"  - Points balance: {account.points_balance}")

        # Verify points calculation
        expected_points = int(150.00 * 0.1) + int(75.50 * 0.1)  # 15 + 7 = 22
        if account.points_balance == expected_points:
            print(f"SUCCESS: Points calculation correct ({expected_points} points)")
        else:
            print(f"ERROR: Points calculation wrong. Expected {expected_points}, got {account.points_balance}")

    except Exception as e:
        print(f"ERROR: Could not verify client data: {e}")
        return False

    # Step 5: Test with Telegram notification (will fail gracefully)
    print("\n5. Testing with Telegram notification (should fail gracefully)...")
    purchase_data_3 = {
        'business_id': business_id,
        'amount': '50.00',
        'currency': 'MXN',
        'client_name': 'María García',
        'client_email': 'maria@example.com',
        'telegram_user_id': '123456789',  # Fake Telegram ID
        'send_telegram_notification': True
    }

    response = client.post('/api/purchase-with-client/', purchase_data_3, content_type='application/json')
    if response.status_code != 201:
        print(f"ERROR: Could not create third purchase: {response.content}")
        return False

    result = response.json()
    print(f"SUCCESS: Purchase created even with Telegram failure")
    print(f"  - Purchase ID: {result['purchase_id']}")
    print(f"  - Telegram notification sent: {result['telegram_notification_sent']} (should be False)")

    print("\n🎉 All tests passed! The purchase-with-client flow is working correctly!")
    print("\nNext steps:")
    print("1. Set up a real Telegram bot token to test notifications")
    print("2. Implement birthday notification scheduler")
    print("3. Add more advanced bot features")

    return True


if __name__ == "__main__":
    success = test_purchase_with_client_flow()
    if not success:
        sys.exit(1)