from rest_framework import serializers
from .models import Business, Client, LoyaltyAccount, Purchase, PointEvent


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['business_id', 'name', 'email', 'timezone', 'points_per_currency', 
                 'birthday_bonus_points', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['business_id', 'created_at', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = Client
        fields = ['client_id', 'business', 'business_name', 'name', 'email', 'phone', 
                 'birthday', 'joined_at', 'created_at', 'updated_at']
        read_only_fields = ['client_id', 'created_at', 'updated_at']


class LoyaltyAccountSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = LoyaltyAccount
        fields = ['account_id', 'business', 'business_name', 'client', 'client_name', 
                 'points_balance', 'updated_at']
        read_only_fields = ['account_id', 'updated_at']


class PurchaseSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = Purchase
        fields = ['purchase_id', 'business', 'business_name', 'client', 'client_name', 
                 'amount', 'currency', 'purchased_at', 'created_at']
        read_only_fields = ['purchase_id', 'created_at']


class PointEventSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = PointEvent
        fields = ['event_id', 'business', 'business_name', 'client', 'client_name', 
                 'source', 'source_display', 'points', 'related_purchase', 'note', 
                 'occurred_at', 'created_at']
        read_only_fields = ['event_id', 'created_at']


class PurchaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['business', 'client', 'amount', 'currency']
        
    def create(self, validated_data):
        from .services import PurchaseService
        return PurchaseService.create_purchase_with_points(**validated_data)