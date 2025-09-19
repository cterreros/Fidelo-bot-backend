#!/usr/bin/env python3
"""
Test script for JWT Authentication
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

def test_jwt_authentication():
    """Test JWT authentication flow"""
    print("Testing JWT Authentication...")

    # Create test user if it doesn't exist
    username = 'testuser'
    password = 'testpass123'

    try:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password(password)
            user.save()
            print(f"SUCCESS: Created test user: {username}")
        else:
            print(f"SUCCESS: Using existing test user: {username}")
    except Exception as e:
        print(f"ERROR: Error creating user: {e}")
        return

    # Test with Django test client
    client = Client()

    # Test 1: Get token
    print("\n1. Testing token obtain...")
    try:
        response = client.post('/auth/token/', {
            'username': username,
            'password': password
        }, content_type='application/json')

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access']
            refresh_token = token_data['refresh']
            print(f"SUCCESS: Got access token: {access_token[:50]}...")
            print(f"SUCCESS: Got refresh token: {refresh_token[:50]}...")
        else:
            print(f"ERROR: Token obtain failed: {response.status_code}")
            print(f"Response: {response.content}")
            return
    except Exception as e:
        print(f"ERROR: Error getting token: {e}")
        return

    # Test 2: Access protected endpoint
    print("\n2. Testing protected endpoint access...")
    try:
        response = client.get('/api/businesses/',
                            HTTP_AUTHORIZATION=f'Bearer {access_token}')

        if response.status_code == 200:
            print(f"SUCCESS: Protected endpoint accessible: {response.status_code}")
        else:
            print(f"ERROR: Protected endpoint failed: {response.status_code}")
            print(f"Response: {response.content}")
    except Exception as e:
        print(f"ERROR: Error accessing protected endpoint: {e}")

    # Test 3: Access without token (should fail)
    print("\n3. Testing access without token...")
    try:
        response = client.get('/api/businesses/')

        if response.status_code == 401:
            print(f"SUCCESS: Unauthorized access properly blocked: {response.status_code}")
        else:
            print(f"WARNING: Unexpected status without token: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Error testing unauthorized access: {e}")

    # Test 4: Refresh token
    print("\n4. Testing token refresh...")
    try:
        response = client.post('/auth/token/refresh/', {
            'refresh': refresh_token
        }, content_type='application/json')

        if response.status_code == 200:
            new_token_data = response.json()
            new_access_token = new_token_data['access']
            print(f"SUCCESS: Token refreshed successfully: {new_access_token[:50]}...")
        else:
            print(f"ERROR: Token refresh failed: {response.status_code}")
            print(f"Response: {response.content}")
    except Exception as e:
        print(f"ERROR: Error refreshing token: {e}")

    print("\nJWT Authentication test completed!")
    print("\nNext steps:")
    print("1. Add business-level authorization")
    print("2. Create custom permissions")
    print("3. Add user registration endpoint")

if __name__ == "__main__":
    test_jwt_authentication()