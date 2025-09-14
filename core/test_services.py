import pytest
from decimal import Decimal
from django.db import transaction
from django.test import TransactionTestCase

from core.models import Business, Client, LoyaltyAccount, Purchase, PointEvent
from core.services import PurchaseService, PointsService, ClientService
from conftest import BusinessFactory, ClientFactory, LoyaltyAccountFactory


@pytest.mark.django_db
class TestPurchaseService:
    def test_create_purchase_with_points(self):
        """Test creating a purchase automatically calculates and awards points"""
        business = BusinessFactory(points_per_currency=Decimal('0.1'))  # 1 point per $10
        client = ClientFactory(business=business)
        
        # Create purchase
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=Decimal('100.00'),
            currency='MXN'
        )
        
        # Verify purchase was created
        assert purchase.business == business
        assert purchase.client == client
        assert purchase.amount == Decimal('100.00')
        assert purchase.currency == 'MXN'
        
        # Verify point event was created
        point_events = PointEvent.objects.filter(client=client)
        assert point_events.count() == 1
        
        event = point_events.first()
        assert event.source == PointEvent.Source.PURCHASE
        assert event.points == 10  # 100 * 0.1
        assert event.related_purchase == purchase
        assert "Points for purchase $100.00 MXN" in event.note
        
        # Verify loyalty account was updated
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 10

    def test_create_purchase_with_different_points_rate(self):
        """Test purchase with different points rate configuration"""
        business = BusinessFactory(points_per_currency=Decimal('0.05'))  # 1 point per $20
        client = ClientFactory(business=business)
        
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=Decimal('200.00')
        )
        
        # Verify points calculation
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.PURCHASE)
        assert event.points == 10  # 200 * 0.05
        
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 10

    def test_create_purchase_fractional_points(self):
        """Test purchase with fractional points (should be rounded down)"""
        business = BusinessFactory(points_per_currency=Decimal('0.1'))
        client = ClientFactory(business=business)
        
        # Amount that would give 7.5 points
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=Decimal('75.00')
        )
        
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.PURCHASE)
        assert event.points == 7  # int(75 * 0.1) = 7
        
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 7

    def test_create_purchase_zero_amount(self):
        """Test purchase with zero amount gives zero points"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=Decimal('0.00')
        )
        
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.PURCHASE)
        assert event.points == 0
        
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 0


@pytest.mark.django_db
class TestPointsService:
    def test_calculate_points_for_purchase(self):
        """Test points calculation for different amounts"""
        business = BusinessFactory(points_per_currency=Decimal('0.1'))
        
        # Test various amounts
        assert PointsService.calculate_points_for_purchase(business, Decimal('100')) == 10
        assert PointsService.calculate_points_for_purchase(business, Decimal('50.50')) == 5
        assert PointsService.calculate_points_for_purchase(business, Decimal('9.99')) == 0
        assert PointsService.calculate_points_for_purchase(business, Decimal('0')) == 0

    def test_calculate_points_negative_amount(self):
        """Test points calculation handles negative amounts"""
        business = BusinessFactory(points_per_currency=Decimal('0.1'))
        
        # Negative amount should give 0 points (max with 0)
        points = PointsService.calculate_points_for_purchase(business, Decimal('-50'))
        assert points == 0

    def test_update_loyalty_account_new_client(self):
        """Test updating loyalty account for new client (creates account)"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        
        # Client shouldn't have account yet
        assert not LoyaltyAccount.objects.filter(client=client).exists()
        
        # Update points
        account = PointsService.update_loyalty_account(client, 50)
        
        assert account.client == client
        assert account.business == business
        assert account.points_balance == 50

    def test_update_loyalty_account_existing_client(self):
        """Test updating loyalty account for existing client"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        existing_account = LoyaltyAccountFactory(
            business=business, 
            client=client, 
            points_balance=100
        )
        
        # Update points
        account = PointsService.update_loyalty_account(client, 25)
        
        # Should be same account, updated balance
        assert account.account_id == existing_account.account_id
        assert account.points_balance == 125

    def test_update_loyalty_account_negative_points(self):
        """Test updating loyalty account with negative points (deduction)"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        LoyaltyAccountFactory(business=business, client=client, points_balance=100)
        
        # Deduct points
        account = PointsService.update_loyalty_account(client, -30)
        assert account.points_balance == 70

    def test_award_birthday_bonus(self):
        """Test awarding birthday bonus"""
        business = BusinessFactory(birthday_bonus_points=75)
        client = ClientFactory(business=business)
        
        # Award birthday bonus
        account = PointsService.award_birthday_bonus(client)
        
        # Verify point event was created
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.BIRTHDAY)
        assert event.points == 75
        assert event.note == "Birthday bonus"
        
        # Verify account was updated
        assert account.points_balance == 75

    def test_award_birthday_bonus_existing_points(self):
        """Test awarding birthday bonus to client with existing points"""
        business = BusinessFactory(birthday_bonus_points=50)
        client = ClientFactory(business=business)
        LoyaltyAccountFactory(business=business, client=client, points_balance=25)
        
        account = PointsService.award_birthday_bonus(client)
        
        # Should add to existing balance
        assert account.points_balance == 75

    def test_manual_adjustment_positive(self):
        """Test manual positive points adjustment"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        
        account = PointsService.manual_adjustment(client, 100, "Compensation points")
        
        # Verify point event
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.ADJUSTMENT)
        assert event.points == 100
        assert event.note == "Compensation points"
        
        # Verify account
        assert account.points_balance == 100

    def test_manual_adjustment_negative(self):
        """Test manual negative points adjustment"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        LoyaltyAccountFactory(business=business, client=client, points_balance=150)
        
        account = PointsService.manual_adjustment(client, -50, "Point correction")
        
        # Verify point event
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.ADJUSTMENT)
        assert event.points == -50
        assert event.note == "Point correction"
        
        # Verify account
        assert account.points_balance == 100

    def test_manual_adjustment_default_note(self):
        """Test manual adjustment with default note"""
        client = ClientFactory()
        
        PointsService.manual_adjustment(client, 25)
        
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.ADJUSTMENT)
        assert event.note == "Manual adjustment"


@pytest.mark.django_db
class TestClientService:
    def test_create_client_with_account(self):
        """Test creating client automatically creates loyalty account"""
        business = BusinessFactory()
        
        # Create client
        client = ClientService.create_client_with_account(
            business=business,
            name="John Doe",
            email="john@example.com",
            phone="1234567890"
        )
        
        # Verify client was created
        assert client.business == business
        assert client.name == "John Doe"
        assert client.email == "john@example.com"
        assert client.phone == "1234567890"
        assert client.client_id
        
        # Verify loyalty account was created
        account = LoyaltyAccount.objects.get(client=client)
        assert account.business == business
        assert account.client == client
        assert account.points_balance == 0

    def test_create_client_with_optional_fields(self):
        """Test creating client with optional birthday field"""
        from datetime import date
        
        business = BusinessFactory()
        birthday = date(1990, 5, 15)
        
        client = ClientService.create_client_with_account(
            business=business,
            name="Jane Doe",
            email="jane@example.com",
            phone="0987654321",
            birthday=birthday
        )
        
        assert client.birthday == birthday
        
        # Account should still be created
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 0

    def test_create_client_without_optional_fields(self):
        """Test creating client without phone and birthday"""
        business = BusinessFactory()
        
        client = ClientService.create_client_with_account(
            business=business,
            name="Bob Smith",
            email="bob@example.com"
        )
        
        assert client.phone is None
        assert client.birthday is None
        
        # Account should still be created
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 0


@pytest.mark.django_db
class TestServiceIntegration:
    def test_complete_purchase_flow(self):
        """Test complete flow: create client, make purchase, award birthday bonus"""
        business = BusinessFactory(
            points_per_currency=Decimal('0.2'),  # 1 point per $5
            birthday_bonus_points=100
        )
        
        # Create client with account
        client = ClientService.create_client_with_account(
            business=business,
            name="Test Customer",
            email="test@example.com"
        )
        
        # Make a purchase
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=Decimal('250.00')  # Should give 50 points
        )
        
        # Check points after purchase
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 50
        
        # Award birthday bonus
        PointsService.award_birthday_bonus(client)
        
        # Check final points
        account.refresh_from_db()
        assert account.points_balance == 150  # 50 + 100
        
        # Verify all events were recorded
        events = PointEvent.objects.filter(client=client).order_by('created_at')
        assert events.count() == 2
        
        purchase_event = events[0]
        assert purchase_event.source == PointEvent.Source.PURCHASE
        assert purchase_event.points == 50
        assert purchase_event.related_purchase == purchase
        
        birthday_event = events[1]
        assert birthday_event.source == PointEvent.Source.BIRTHDAY
        assert birthday_event.points == 100
        
    def test_multiple_purchases_accumulate_points(self):
        """Test that multiple purchases accumulate points correctly"""
        business = BusinessFactory(points_per_currency=Decimal('0.1'))
        client = ClientFactory(business=business)
        
        # Make multiple purchases
        purchase1 = PurchaseService.create_purchase_with_points(
            business=business, client=client, amount=Decimal('50.00')  # 5 points
        )
        purchase2 = PurchaseService.create_purchase_with_points(
            business=business, client=client, amount=Decimal('75.00')  # 7 points
        )
        purchase3 = PurchaseService.create_purchase_with_points(
            business=business, client=client, amount=Decimal('25.00')  # 2 points
        )
        
        # Check accumulated points
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 14  # 5 + 7 + 2
        
        # Verify all purchase events
        events = PointEvent.objects.filter(
            client=client, 
            source=PointEvent.Source.PURCHASE
        ).order_by('created_at')
        assert events.count() == 3
        assert events[0].points == 5
        assert events[1].points == 7  
        assert events[2].points == 2