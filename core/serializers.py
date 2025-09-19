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


class PurchaseWithClientDataSerializer(serializers.Serializer):
    """
    Serializer for creating purchases with automatic client creation/update.
    Ideal for POS systems that send customer data with each purchase.
    """
    # Business info
    business_id = serializers.UUIDField()

    # Purchase info
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=8, default='MXN')

    # Client info
    client_name = serializers.CharField(max_length=160)
    client_email = serializers.EmailField()
    client_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    client_birthday = serializers.DateField(required=False, allow_null=True)

    # Telegram integration
    telegram_user_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    send_telegram_notification = serializers.BooleanField(default=True)

    # SMS integration
    send_sms_notification = serializers.BooleanField(default=True)

    def create(self, validated_data):
        from .services import PurchaseService
        # Extract business
        business_id = validated_data.pop('business_id')
        business = Business.objects.get(business_id=business_id)

        # Extract client data
        client_data = {
            'name': validated_data.pop('client_name'),
            'email': validated_data.pop('client_email'),
            'phone': validated_data.pop('client_phone', None),
            'birthday': validated_data.pop('client_birthday', None),
        }

        # Handle notifications
        telegram_user_id = validated_data.pop('telegram_user_id', None)
        send_telegram_notification = validated_data.pop('send_telegram_notification', True)
        send_sms_notification = validated_data.pop('send_sms_notification', True)

        # Get or create client
        client, created = Client.objects.get_or_create(
            business=business,
            email=client_data['email'],
            defaults=client_data
        )

        # Update client info if exists but data changed
        if not created:
            for field, value in client_data.items():
                if value and getattr(client, field) != value:
                    setattr(client, field, value)
            client.save()

        # Create purchase with points
        purchase = PurchaseService.create_purchase_with_points(
            business=business,
            client=client,
            amount=validated_data['amount'],
            currency=validated_data.get('currency', 'MXN')
        )

        # Send notifications
        telegram_notification_sent = False
        sms_notification_sent = False

        # Send Telegram notification if enabled
        if send_telegram_notification and telegram_user_id:
            try:
                from .telegram_notifications_sync import send_purchase_notification
                telegram_notification_sent = send_purchase_notification(
                    telegram_user_id=telegram_user_id,
                    client_id=str(client.client_id),
                    purchase_id=str(purchase.purchase_id),
                    is_new_client=created
                )
            except Exception as e:
                # Log error but don't fail the purchase
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send Telegram notification: {e}")

        # Send SMS notification if enabled
        if send_sms_notification and client_data.get('phone'):
            try:
                from .sms_service import sms_service
                from .models import LoyaltyAccount
                points_earned = int(purchase.amount * business.points_per_currency)

                try:
                    account = LoyaltyAccount.objects.get(client=client)
                    total_points = account.points_balance
                except LoyaltyAccount.DoesNotExist:
                    total_points = points_earned

                sms_notification_sent = sms_service.send_purchase_notification_sms(
                    client_phone=client_data['phone'],
                    client_name=client_data['name'],
                    business_name=business.name,
                    points_earned=points_earned,
                    total_points=total_points,
                    bot_username="FideloBot"
                )
            except Exception as e:
                # Log error but don't fail the purchase
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send SMS notification: {e}")

        return {
            'purchase': purchase,
            'client': client,
            'created_new_client': created,
            'telegram_notification_sent': telegram_notification_sent,
            'sms_notification_sent': sms_notification_sent
        }