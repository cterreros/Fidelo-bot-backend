from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from .models import Business, Client, LoyaltyAccount, Purchase, PointEvent
from .serializers import (
    BusinessSerializer, ClientSerializer, LoyaltyAccountSerializer,
    PurchaseSerializer, PointEventSerializer, PurchaseCreateSerializer,
    PurchaseWithClientDataSerializer
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
        queryset = Client.objects.all()
        business_id = self.request.query_params.get('business_id')
        phone = self.request.query_params.get('phone')

        if business_id:
            queryset = queryset.filter(business__business_id=business_id)

        if phone:
            queryset = queryset.filter(phone=phone)

        return queryset
    
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


class PurchaseWithClientDataView(APIView):
    """
    Endpoint for POS systems to create purchases with automatic client management
    Supports Telegram notifications
    """

    def post(self, request):
        """
        Create a purchase with automatic client creation/update and optional Telegram notification

        Expected payload:
        {
            "business_id": "uuid",
            "amount": "100.00",
            "currency": "MXN",
            "client_name": "Juan Pérez",
            "client_email": "juan@example.com",
            "client_phone": "+52123456789",
            "client_birthday": "1990-05-15",
            "telegram_user_id": "123456789",
            "send_telegram_notification": true
        }
        """
        serializer = PurchaseWithClientDataSerializer(data=request.data)

        if serializer.is_valid():
            try:
                result = serializer.save()

                response_data = {
                    'success': True,
                    'message': 'Purchase created successfully',
                    'purchase_id': str(result['purchase'].purchase_id),
                    'client_id': str(result['client'].client_id),
                    'created_new_client': result['created_new_client'],
                    'points_earned': int(result['purchase'].amount * result['client'].business.points_per_currency),
                    'client_points_balance': LoyaltyAccount.objects.get(client=result['client']).points_balance,
                    'telegram_notification_sent': result['telegram_notification_sent'],
                    'sms_notification_sent': result['sms_notification_sent']
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'Error creating purchase: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


def purchase_form_view(request):
    """
    Vista para mostrar el formulario de registro de compras con autenticación por negocio
    """
    # Handle business login/logout
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            business_id = request.POST.get('business_id')
            try:
                business = Business.objects.get(business_id=business_id, is_active=True)
                request.session['current_business_id'] = str(business.business_id)
                request.session['current_business_name'] = business.name
                return JsonResponse({
                    'success': True,
                    'business_name': business.name,
                    'business_id': str(business.business_id)
                })
            except Business.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Negocio no encontrado'})

        elif action == 'logout':
            request.session.pop('current_business_id', None)
            request.session.pop('current_business_name', None)
            return JsonResponse({'success': True})

    # Get current business from session
    current_business = None
    current_business_id = request.session.get('current_business_id')

    if current_business_id:
        try:
            current_business = Business.objects.get(business_id=current_business_id, is_active=True)
        except Business.DoesNotExist:
            # Clear invalid session
            request.session.pop('current_business_id', None)
            request.session.pop('current_business_name', None)

    # Get all available businesses
    businesses = Business.objects.filter(is_active=True).order_by('name')

    context = {
        'current_business': current_business,
        'businesses': businesses,
    }

    return render(request, 'purchase_form.html', context)
