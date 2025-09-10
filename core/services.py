from decimal import Decimal
from django.db import transaction
from .models import Business, Client, LoyaltyAccount, Purchase, PointEvent


class PurchaseService:
    @staticmethod
    @transaction.atomic
    def create_purchase_with_points(business, client, amount, currency='MXN'):
        """
        Creates a purchase and automatically calculates and awards points
        """
        # Create the purchase
        purchase = Purchase.objects.create(
            business=business,
            client=client,
            amount=amount,
            currency=currency
        )
        
        # Calculate points based on business configuration
        points_earned = PointsService.calculate_points_for_purchase(business, amount)
        
        # Create point event
        PointEvent.objects.create(
            business=business,
            client=client,
            source=PointEvent.Source.PURCHASE,
            points=points_earned,
            related_purchase=purchase,
            note=f"Points for purchase ${amount} {currency}"
        )
        
        # Update loyalty account
        PointsService.update_loyalty_account(client, points_earned)
        
        return purchase


class PointsService:
    @staticmethod
    def calculate_points_for_purchase(business, amount):
        """
        Calculate points based on business configuration
        Default: 0.1 points per currency unit (1 point per $10)
        """
        points = int(amount * business.points_per_currency)
        return max(points, 0)  # Ensure non-negative points
    
    @staticmethod
    @transaction.atomic
    def update_loyalty_account(client, points_delta):
        """
        Update loyalty account balance
        """
        account, created = LoyaltyAccount.objects.get_or_create(
            client=client,
            business=client.business,
            defaults={'points_balance': 0}
        )
        
        account.points_balance += points_delta
        account.save()
        return account
    
    @staticmethod
    @transaction.atomic
    def award_birthday_bonus(client):
        """
        Award birthday bonus points
        """
        business = client.business
        bonus_points = business.birthday_bonus_points
        
        # Create point event
        PointEvent.objects.create(
            business=business,
            client=client,
            source=PointEvent.Source.BIRTHDAY,
            points=bonus_points,
            note="Birthday bonus"
        )
        
        # Update loyalty account
        return PointsService.update_loyalty_account(client, bonus_points)
    
    @staticmethod
    @transaction.atomic
    def manual_adjustment(client, points, note="Manual adjustment"):
        """
        Manual points adjustment (positive or negative)
        """
        # Create point event
        PointEvent.objects.create(
            business=client.business,
            client=client,
            source=PointEvent.Source.ADJUSTMENT,
            points=points,
            note=note
        )
        
        # Update loyalty account
        return PointsService.update_loyalty_account(client, points)


class ClientService:
    @staticmethod
    @transaction.atomic
    def create_client_with_account(business, name, email, phone=None, birthday=None):
        """
        Create a client and automatically create their loyalty account
        """
        client = Client.objects.create(
            business=business,
            name=name,
            email=email,
            phone=phone,
            birthday=birthday
        )
        
        # Create loyalty account
        LoyaltyAccount.objects.create(
            business=business,
            client=client,
            points_balance=0
        )
        
        return client