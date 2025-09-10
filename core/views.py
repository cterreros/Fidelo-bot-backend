from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Business, Client, LoyaltyAccount, Purchase, PointEvent
from .serializers import (
    BusinessSerializer, ClientSerializer, LoyaltyAccountSerializer,
    PurchaseSerializer, PointEventSerializer, PurchaseCreateSerializer
)
from .services import ClientService, PointsService


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    
    def get_queryset(self):
        queryset = Business.objects.filter(is_active=True)
        return queryset


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    
    def get_queryset(self):
        business_id = self.request.query_params.get('business_id')
        if business_id:
            return Client.objects.filter(business__business_id=business_id)
        return Client.objects.all()
    
    def perform_create(self, serializer):
        client = ClientService.create_client_with_account(**serializer.validated_data)
        serializer.instance = client
    
    @action(detail=True, methods=['get'])
    def points_balance(self, request, pk=None):
        """Get client's current points balance"""
        client = self.get_object()
        try:
            account = LoyaltyAccount.objects.get(client=client)
            return Response({'points_balance': account.points_balance})
        except LoyaltyAccount.DoesNotExist:
            return Response({'points_balance': 0})
    
    @action(detail=True, methods=['post'])
    def award_birthday_bonus(self, request, pk=None):
        """Award birthday bonus to client"""
        client = self.get_object()
        account = PointsService.award_birthday_bonus(client)
        return Response({
            'message': 'Birthday bonus awarded',
            'bonus_points': client.business.birthday_bonus_points,
            'new_balance': account.points_balance
        })


class LoyaltyAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoyaltyAccount.objects.all()
    serializer_class = LoyaltyAccountSerializer
    
    def get_queryset(self):
        business_id = self.request.query_params.get('business_id')
        if business_id:
            return LoyaltyAccount.objects.filter(business__business_id=business_id)
        return LoyaltyAccount.objects.all()


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseCreateSerializer
        return PurchaseSerializer
    
    def get_queryset(self):
        queryset = Purchase.objects.all()
        business_id = self.request.query_params.get('business_id')
        client_id = self.request.query_params.get('client_id')
        
        if business_id:
            queryset = queryset.filter(business__business_id=business_id)
        if client_id:
            queryset = queryset.filter(client__client_id=client_id)
            
        return queryset.order_by('-purchased_at')


class PointEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PointEvent.objects.all()
    serializer_class = PointEventSerializer
    
    def get_queryset(self):
        queryset = PointEvent.objects.all()
        business_id = self.request.query_params.get('business_id')
        client_id = self.request.query_params.get('client_id')
        source = self.request.query_params.get('source')
        
        if business_id:
            queryset = queryset.filter(business__business_id=business_id)
        if client_id:
            queryset = queryset.filter(client__client_id=client_id)
        if source:
            queryset = queryset.filter(source=source)
            
        return queryset.order_by('-occurred_at')
