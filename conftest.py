import pytest
import os
import django
from django.conf import settings
import factory

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from core.models import Business, Client, LoyaltyAccount, Purchase, PointEvent


@pytest.fixture(scope='session')
def django_db_setup():
    """Use SQLite in-memory database for testing"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': False,
    }


class BusinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Business
        django_get_or_create = ('email',)
    
    name = factory.Faker('company')
    email = factory.Faker('email')
    timezone = 'America/Mexico_City'
    points_per_currency = 0.1
    birthday_bonus_points = 50
    is_active = True


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client
        django_get_or_create = ('business', 'email')
    
    business = factory.SubFactory(BusinessFactory)
    name = factory.Faker('name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    birthday = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)


class LoyaltyAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoyaltyAccount
    
    business = factory.SubFactory(BusinessFactory)
    client = factory.SubFactory(ClientFactory)
    points_balance = 0


class PurchaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Purchase
    
    business = factory.SubFactory(BusinessFactory)
    client = factory.SubFactory(ClientFactory)
    amount = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    currency = 'MXN'


class PointEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PointEvent
    
    business = factory.SubFactory(BusinessFactory)
    client = factory.SubFactory(ClientFactory)
    source = PointEvent.Source.PURCHASE
    points = factory.Faker('random_int', min=1, max=100)
    note = factory.Faker('sentence')


@pytest.fixture
def business():
    """Create a test business"""
    return BusinessFactory()


@pytest.fixture
def client(business):
    """Create a test client"""
    return ClientFactory(business=business)


@pytest.fixture
def loyalty_account(business, client):
    """Create a test loyalty account"""
    return LoyaltyAccountFactory(business=business, client=client)


@pytest.fixture
def purchase(business, client):
    """Create a test purchase"""
    return PurchaseFactory(business=business, client=client)


@pytest.fixture
def point_event(business, client):
    """Create a test point event"""
    return PointEventFactory(business=business, client=client)