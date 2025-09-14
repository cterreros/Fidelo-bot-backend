import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date

from core.models import Business, Client, LoyaltyAccount, Purchase, PointEvent
from conftest import BusinessFactory, ClientFactory, LoyaltyAccountFactory, PurchaseFactory


@pytest.mark.django_db
class TestBusinessAPI:
    def setup_method(self):
        self.client = APIClient()
        
    def test_list_businesses(self):
        """Test listing businesses"""
        # Create test businesses
        business1 = BusinessFactory(name="Business 1", is_active=True)
        business2 = BusinessFactory(name="Business 2", is_active=True)
        BusinessFactory(name="Inactive Business", is_active=False)  # Should be filtered
        
        response = self.client.get('/api/businesses/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Only active businesses
        
        names = [b['name'] for b in response.data]
        assert "Business 1" in names
        assert "Business 2" in names
        assert "Inactive Business" not in names

    def test_create_business(self):
        """Test creating a business"""
        business_data = {
            'name': 'New Business',
            'email': 'new@business.com',
            'timezone': 'America/New_York',
            'points_per_currency': '0.05',
            'birthday_bonus_points': 75
        }
        
        response = self.client.post('/api/businesses/', business_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Business'
        assert response.data['email'] == 'new@business.com'
        assert response.data['points_per_currency'] == '0.050'
        assert response.data['birthday_bonus_points'] == 75
        assert 'business_id' in response.data

    def test_retrieve_business(self):
        """Test retrieving a single business"""
        business = BusinessFactory()
        
        response = self.client.get(f'/api/businesses/{business.business_id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == business.name
        assert response.data['business_id'] == str(business.business_id)

    def test_update_business(self):
        """Test updating a business"""
        business = BusinessFactory(name="Original Name")
        
        update_data = {
            'name': 'Updated Name',
            'email': business.email,
            'birthday_bonus_points': 100
        }
        
        response = self.client.put(f'/api/businesses/{business.business_id}/', update_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'
        assert response.data['birthday_bonus_points'] == 100


@pytest.mark.django_db 
class TestClientAPI:
    def setup_method(self):
        self.client = APIClient()
        self.business = BusinessFactory()

    def test_list_clients(self):
        """Test listing clients"""
        client1 = ClientFactory(business=self.business, name="Client 1")
        client2 = ClientFactory(business=self.business, name="Client 2")
        other_business = BusinessFactory()
        ClientFactory(business=other_business, name="Other Client")
        
        # Filter by business
        response = self.client.get(f'/api/clients/?business_id={self.business.business_id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        names = [c['name'] for c in response.data]
        assert "Client 1" in names
        assert "Client 2" in names
        assert "Other Client" not in names

    def test_create_client(self):
        """Test creating a client (should create loyalty account automatically)"""
        client_data = {
            'business': str(self.business.business_id),
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'birthday': '1990-05-15'
        }
        
        response = self.client.post('/api/clients/', client_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'John Doe'
        assert response.data['email'] == 'john@example.com'
        assert response.data['business_name'] == self.business.name
        
        # Verify loyalty account was created
        client = Client.objects.get(client_id=response.data['client_id'])
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == 0

    def test_client_points_balance(self):
        """Test getting client's points balance"""
        client = ClientFactory(business=self.business)
        LoyaltyAccountFactory(business=self.business, client=client, points_balance=150)
        
        response = self.client.get(f'/api/clients/{client.client_id}/points_balance/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['points_balance'] == 150

    def test_client_points_balance_no_account(self):
        """Test getting points balance for client with no account"""
        client = ClientFactory(business=self.business)
        
        response = self.client.get(f'/api/clients/{client.client_id}/points_balance/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['points_balance'] == 0

    def test_award_birthday_bonus(self):
        """Test awarding birthday bonus to client"""
        client = ClientFactory(business=self.business)
        
        response = self.client.post(f'/api/clients/{client.client_id}/award_birthday_bonus/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Birthday bonus awarded'
        assert response.data['bonus_points'] == self.business.birthday_bonus_points
        
        # Verify account was updated
        account = LoyaltyAccount.objects.get(client=client)
        assert account.points_balance == self.business.birthday_bonus_points
        
        # Verify event was created
        event = PointEvent.objects.get(client=client, source=PointEvent.Source.BIRTHDAY)
        assert event.points == self.business.birthday_bonus_points


@pytest.mark.django_db
class TestPurchaseAPI:
    def setup_method(self):
        self.client = APIClient()
        self.business = BusinessFactory(points_per_currency=Decimal('0.1'))
        self.customer = ClientFactory(business=self.business)

    def test_list_purchases(self):
        """Test listing purchases"""
        purchase1 = PurchaseFactory(business=self.business, client=self.customer)
        purchase2 = PurchaseFactory(business=self.business, client=self.customer)
        other_business = BusinessFactory()
        PurchaseFactory(business=other_business)  # Should be filtered
        
        response = self.client.get(f'/api/purchases/?business_id={self.business.business_id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_purchase(self):
        """Test creating a purchase (should award points automatically)"""
        purchase_data = {
            'business': str(self.business.business_id),
            'client': str(self.customer.client_id),
            'amount': '100.00',
            'currency': 'MXN'
        }
        
        response = self.client.post('/api/purchases/', purchase_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == '100.00'
        assert response.data['currency'] == 'MXN'
        
        # Verify points were awarded
        account = LoyaltyAccount.objects.get(client=self.customer)
        assert account.points_balance == 10  # 100 * 0.1
        
        # Verify point event was created
        event = PointEvent.objects.get(client=self.customer, source=PointEvent.Source.PURCHASE)
        assert event.points == 10

    def test_list_purchases_by_client(self):
        """Test filtering purchases by client"""
        client2 = ClientFactory(business=self.business)
        
        purchase1 = PurchaseFactory(business=self.business, client=self.customer)
        PurchaseFactory(business=self.business, client=client2)
        
        response = self.client.get(f'/api/purchases/?client_id={self.customer.client_id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        # API returns UUID as string
        assert str(response.data[0]['client']) == str(self.customer.client_id)


@pytest.mark.django_db
class TestLoyaltyAccountAPI:
    def setup_method(self):
        self.client = APIClient()
        self.business = BusinessFactory()

    def test_list_loyalty_accounts(self):
        """Test listing loyalty accounts"""
        client1 = ClientFactory(business=self.business)
        client2 = ClientFactory(business=self.business)
        account1 = LoyaltyAccountFactory(business=self.business, client=client1, points_balance=100)
        account2 = LoyaltyAccountFactory(business=self.business, client=client2, points_balance=200)
        
        # Filter by business
        response = self.client.get(f'/api/loyalty-accounts/?business_id={self.business.business_id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        balances = [a['points_balance'] for a in response.data]
        assert 100 in balances
        assert 200 in balances

    def test_retrieve_loyalty_account(self):
        """Test retrieving a single loyalty account"""
        client = ClientFactory(business=self.business, name="Test Client")
        account = LoyaltyAccountFactory(
            business=self.business, 
            client=client, 
            points_balance=150
        )
        
        response = self.client.get(f'/api/loyalty-accounts/{account.account_id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['points_balance'] == 150
        assert response.data['client_name'] == "Test Client"
        assert response.data['business_name'] == self.business.name


@pytest.mark.django_db
class TestPointEventAPI:
    def setup_method(self):
        self.client = APIClient()
        self.business = BusinessFactory()
        self.customer = ClientFactory(business=self.business)

    def test_list_point_events(self):
        """Test listing point events"""
        # Create different types of events
        purchase = PurchaseFactory(business=self.business, client=self.customer)
        
        from core.services import PointsService
        
        # Create events using services (more realistic)
        PointsService.manual_adjustment(self.customer, 50, "Test adjustment")
        PointsService.award_birthday_bonus(self.customer)
        
        response = self.client.get(f'/api/point-events/?client_id={self.customer.client_id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        sources = [e['source'] for e in response.data]
        assert 'adjustment' in sources
        assert 'birthday' in sources

    def test_filter_point_events_by_source(self):
        """Test filtering point events by source"""
        from core.services import PointsService
        
        PointsService.manual_adjustment(self.customer, 25, "Adjustment")
        PointsService.award_birthday_bonus(self.customer)
        
        response = self.client.get(f'/api/point-events/?client_id={self.customer.client_id}&source=birthday')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['source'] == 'birthday'


@pytest.mark.django_db 
class TestAPIIntegration:
    def setup_method(self):
        self.client = APIClient()

    def test_complete_loyalty_flow_via_api(self):
        """Test complete loyalty flow through API endpoints"""
        # 1. Create business
        business_data = {
            'name': 'Test Store',
            'email': 'store@test.com',
            'points_per_currency': '0.2',  # 1 point per $5
            'birthday_bonus_points': 100
        }
        response = self.client.post('/api/businesses/', business_data)
        assert response.status_code == status.HTTP_201_CREATED
        business_id = response.data['business_id']
        
        # 2. Create customer 
        client_data = {
            'business': business_id,
            'name': 'Test Customer',
            'email': 'customer@test.com',
            'birthday': '1990-01-01'
        }
        response = self.client.post('/api/clients/', client_data)
        assert response.status_code == status.HTTP_201_CREATED
        client_id = response.data['client_id']
        
        # 3. Check initial points (should be 0)
        response = self.client.get(f'/api/clients/{client_id}/points_balance/')
        assert response.data['points_balance'] == 0
        
        # 4. Make purchase
        purchase_data = {
            'business': business_id,
            'client': client_id,
            'amount': '150.00',
            'currency': 'USD'
        }
        response = self.client.post('/api/purchases/', purchase_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 5. Check points after purchase (150 * 0.2 = 30 points)
        response = self.client.get(f'/api/clients/{client_id}/points_balance/')
        assert response.data['points_balance'] == 30
        
        # 6. Award birthday bonus
        response = self.client.post(f'/api/clients/{client_id}/award_birthday_bonus/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['new_balance'] == 130  # 30 + 100
        
        # 7. Check final points
        response = self.client.get(f'/api/clients/{client_id}/points_balance/')
        assert response.data['points_balance'] == 130
        
        # 8. Verify all events were recorded
        response = self.client.get(f'/api/point-events/?client_id={client_id}')
        assert len(response.data) == 2  # Purchase + Birthday
        
        sources = [event['source'] for event in response.data]
        assert 'purchase' in sources
        assert 'birthday' in sources

    def test_multiple_client_isolation(self):
        """Test that clients' points are properly isolated"""
        business = BusinessFactory()
        client1 = ClientFactory(business=business, name="Client 1")
        client2 = ClientFactory(business=business, name="Client 2")
        
        # Client 1 makes purchase
        purchase1_data = {
            'business': str(business.business_id),
            'client': str(client1.client_id),
            'amount': '50.00'
        }
        response = self.client.post('/api/purchases/', purchase1_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Client 2 makes different purchase  
        purchase2_data = {
            'business': str(business.business_id),
            'client': str(client2.client_id),
            'amount': '100.00'
        }
        response = self.client.post('/api/purchases/', purchase2_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check each client's points separately
        response1 = self.client.get(f'/api/clients/{client1.client_id}/points_balance/')
        response2 = self.client.get(f'/api/clients/{client2.client_id}/points_balance/')
        
        assert response1.data['points_balance'] == 5   # 50 * 0.1
        assert response2.data['points_balance'] == 10  # 100 * 0.1