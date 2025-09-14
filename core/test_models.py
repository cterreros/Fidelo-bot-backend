import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from core.models import Business, Client, LoyaltyAccount, Purchase, PointEvent
from conftest import BusinessFactory, ClientFactory, LoyaltyAccountFactory, PurchaseFactory, PointEventFactory


@pytest.mark.django_db
class TestBusinessModel:
    def test_create_business(self):
        """Test creating a business with valid data"""
        business = BusinessFactory()
        assert business.name
        assert business.email
        assert business.business_id
        assert business.points_per_currency == 0.1
        assert business.birthday_bonus_points == 50
        assert business.is_active is True
        assert business.timezone == 'America/Mexico_City'

    def test_business_str_representation(self):
        """Test business string representation"""
        business = BusinessFactory(name="Test Business")
        assert str(business) == "Test Business"

    def test_business_allows_duplicate_email(self):
        """Test that business email can be duplicated (no unique constraint)"""
        email = "test@example.com"
        
        # Create businesses directly to avoid factory get_or_create
        business1 = Business.objects.create(
            name="Business 1",
            email=email
        )
        business2 = Business.objects.create(
            name="Business 2", 
            email=email
        )
        
        assert business1.email == email
        assert business2.email == email
        assert business1.business_id != business2.business_id

    def test_business_points_configuration(self):
        """Test business points configuration"""
        business = BusinessFactory(
            points_per_currency=Decimal('0.05'),
            birthday_bonus_points=100
        )
        assert business.points_per_currency == Decimal('0.05')
        assert business.birthday_bonus_points == 100


@pytest.mark.django_db
class TestClientModel:
    def test_create_client(self):
        """Test creating a client with valid data"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        
        assert client.name
        assert client.email
        assert client.client_id
        assert client.business == business
        assert client.joined_at

    def test_client_str_representation(self):
        """Test client string representation"""
        business = BusinessFactory(name="Test Business")
        client = ClientFactory(name="John Doe", business=business)
        expected = "John Doe (Test Business)"
        assert str(client) == expected

    @pytest.mark.django_db(transaction=True)
    def test_client_unique_email_per_business(self):
        """Test that client email must be unique per business"""
        business = BusinessFactory()
        email = "client@example.com"
        
        # Create client directly to avoid factory get_or_create
        client1 = Client.objects.create(
            business=business,
            name="Client 1",
            email=email
        )
        
        # Same email in same business should fail
        with pytest.raises(IntegrityError):
            Client.objects.create(
                business=business,
                name="Client 2", 
                email=email
            )
        
        # Same email in different business should work
        other_business = BusinessFactory()
        client2 = Client.objects.create(
            business=other_business,
            name="Client 2",
            email=email
        )
        assert client2.email == email

    def test_client_with_birthday(self):
        """Test client with birthday"""
        birthday = date(1990, 5, 15)
        client = ClientFactory(birthday=birthday)
        assert client.birthday == birthday

    def test_client_optional_fields(self):
        """Test client with optional fields"""
        client = ClientFactory(phone=None, birthday=None)
        assert client.phone is None
        assert client.birthday is None


@pytest.mark.django_db
class TestLoyaltyAccountModel:
    def test_create_loyalty_account(self):
        """Test creating a loyalty account"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        account = LoyaltyAccountFactory(business=business, client=client)
        
        assert account.account_id
        assert account.business == business
        assert account.client == client
        assert account.points_balance == 0

    def test_loyalty_account_str_representation(self):
        """Test loyalty account string representation"""
        client = ClientFactory(name="John Doe")
        account = LoyaltyAccountFactory(client=client, points_balance=150)
        expected = "John Doe - 150 points"
        assert str(account) == expected

    def test_loyalty_account_one_per_client(self):
        """Test that each client can have only one loyalty account"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        LoyaltyAccountFactory(business=business, client=client)
        
        # Creating another account for same client should fail
        with pytest.raises(IntegrityError):
            LoyaltyAccountFactory(business=business, client=client)


@pytest.mark.django_db
class TestPurchaseModel:
    def test_create_purchase(self):
        """Test creating a purchase"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        purchase = PurchaseFactory(
            business=business, 
            client=client, 
            amount=Decimal('100.50')
        )
        
        assert purchase.purchase_id
        assert purchase.business == business
        assert purchase.client == client
        assert purchase.amount == Decimal('100.50')
        assert purchase.currency == 'MXN'
        assert purchase.purchased_at
        assert purchase.created_at

    def test_purchase_str_representation(self):
        """Test purchase string representation"""
        client = ClientFactory(name="John Doe")
        purchase = PurchaseFactory(
            client=client, 
            amount=Decimal('250.00'),
            currency='USD'
        )
        expected = "John Doe - $250.00 USD"
        assert str(purchase) == expected

    def test_purchase_ordering(self):
        """Test that purchases are ordered by purchased_at descending"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        
        # Create purchases with different dates
        older_purchase = PurchaseFactory(business=business, client=client)
        older_purchase.purchased_at = timezone.now() - timedelta(days=1)
        older_purchase.save()
        
        newer_purchase = PurchaseFactory(business=business, client=client)
        newer_purchase.purchased_at = timezone.now()
        newer_purchase.save()
        
        purchases = Purchase.objects.filter(business=business)
        assert purchases.first() == newer_purchase
        assert purchases.last() == older_purchase


@pytest.mark.django_db
class TestPointEventModel:
    def test_create_point_event(self):
        """Test creating a point event"""
        business = BusinessFactory()
        client = ClientFactory(business=business)
        purchase = PurchaseFactory(business=business, client=client)
        
        event = PointEventFactory(
            business=business,
            client=client,
            source=PointEvent.Source.PURCHASE,
            points=50,
            related_purchase=purchase
        )
        
        assert event.event_id
        assert event.business == business
        assert event.client == client
        assert event.source == PointEvent.Source.PURCHASE
        assert event.points == 50
        assert event.related_purchase == purchase
        assert event.occurred_at
        assert event.created_at

    def test_point_event_str_representation_positive(self):
        """Test point event string representation for positive points"""
        client = ClientFactory(name="John Doe")
        event = PointEventFactory(
            client=client,
            points=100,
            source=PointEvent.Source.PURCHASE
        )
        expected = "John Doe - +100 pts (Purchase)"
        assert str(event) == expected

    def test_point_event_str_representation_negative(self):
        """Test point event string representation for negative points"""
        client = ClientFactory(name="Jane Doe")
        event = PointEventFactory(
            client=client,
            points=-50,
            source=PointEvent.Source.ADJUSTMENT
        )
        expected = "Jane Doe - -50 pts (Adjustment)"
        assert str(event) == expected

    def test_point_event_sources(self):
        """Test different point event sources"""
        client = ClientFactory()
        
        # Test purchase event
        purchase_event = PointEventFactory(
            client=client,
            source=PointEvent.Source.PURCHASE
        )
        assert purchase_event.get_source_display() == "Purchase"
        
        # Test birthday event
        birthday_event = PointEventFactory(
            client=client,
            source=PointEvent.Source.BIRTHDAY
        )
        assert birthday_event.get_source_display() == "Birthday"
        
        # Test adjustment event
        adjustment_event = PointEventFactory(
            client=client,
            source=PointEvent.Source.ADJUSTMENT
        )
        assert adjustment_event.get_source_display() == "Adjustment"

    def test_point_event_ordering(self):
        """Test that point events are ordered by occurred_at descending"""
        client = ClientFactory()
        
        # Create events with different dates
        older_event = PointEventFactory(client=client)
        older_event.occurred_at = timezone.now() - timedelta(hours=1)
        older_event.save()
        
        newer_event = PointEventFactory(client=client)
        newer_event.occurred_at = timezone.now()
        newer_event.save()
        
        events = PointEvent.objects.filter(client=client)
        assert events.first() == newer_event
        assert events.last() == older_event