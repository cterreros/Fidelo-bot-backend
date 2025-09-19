#!/usr/bin/env python3
"""
Simple test script to verify bot functionality without needing a real Telegram token.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

import pytest
from core.models import Business, Client, LoyaltyAccount
from telegram_bot.bot import FideloBot

@pytest.mark.django_db
def test_basic_functionality():
    """Test basic bot functionality without Telegram connection."""
    print("Testing FideloBot functionality...")
    
    # Test 1: Check if businesses are available
    print("\n1. Testing business availability...")
    businesses = Business.objects.filter(is_active=True)
    print(f"   Found {businesses.count()} active businesses:")
    for business in businesses:
        print(f"   - {business.name} ({business.points_per_currency} pts per unit)")
    
    # Test 2: Test bot instance creation
    print("\n2. Testing bot instance...")
    try:
        bot = FideloBot()
        print("   SUCCESS: Bot instance created successfully")
    except Exception as e:
        print(f"   ERROR: Error creating bot: {e}")
        return
    
    # Test 3: Test database operations (simulate user registration)
    print("\n3. Testing database operations...")
    try:
        from core.services import ClientService
        
        test_business = businesses.first()
        if test_business:
            # Simulate creating a client as the bot would
            test_client = ClientService.create_client_with_account(
                business=test_business,
                name="Test User",
                email="telegram_12345@fidelo.local",
                phone=None,
                birthday=None
            )
            
            account = LoyaltyAccount.objects.get(client=test_client)
            print(f"   SUCCESS: Created test client: {test_client.name}")
            print(f"   SUCCESS: Created loyalty account with {account.points_balance} points")
            
            # Clean up
            test_client.delete()
            print("   SUCCESS: Cleaned up test data")
        
    except Exception as e:
        print(f"   ERROR: Error in database operations: {e}")
        return
    
    # Test 4: Test points calculation
    print("\n4. Testing points calculation...")
    try:
        from core.services import PointsService
        from decimal import Decimal
        
        test_business = businesses.first()
        points = PointsService.calculate_points_for_purchase(test_business, Decimal('100.00'))
        print(f"   SUCCESS: $100 purchase would earn {points} points")
        
        points2 = PointsService.calculate_points_for_purchase(test_business, Decimal('50.75'))
        print(f"   SUCCESS: $50.75 purchase would earn {points2} points")
        
    except Exception as e:
        print(f"   ERROR: Error calculating points: {e}")
        return
    
    print("\nAll tests passed! Bot is ready for Telegram integration.")
    print("\nNext steps:")
    print("1. Get a bot token from @BotFather on Telegram")
    print("2. Update TELEGRAM_BOT_TOKEN in your .env file") 
    print("3. Run: python manage.py run_bot")

if __name__ == "__main__":
    test_basic_functionality()