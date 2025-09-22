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
    client_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    client_email = serializers.EmailField(required=False, allow_blank=True)
    client_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    client_birthday = serializers.DateField(required=False, allow_null=True)

    # Telegram integration
    telegram_user_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    send_telegram_notification = serializers.BooleanField(default=True)

    # SMS integration - TEMPORARILY DISABLED
    send_sms_notification = serializers.BooleanField(default=False)  # Disabled by default

    def create(self, validated_data):
        from .services import PurchaseService
        # Extract business
        business_id = validated_data.pop('business_id')
        business = Business.objects.get(business_id=business_id)

        # Extract client data
        client_data = {
            'name': validated_data.pop('client_name', ''),
            'email': validated_data.pop('client_email', ''),
            'phone': validated_data.pop('client_phone', None),
            'birthday': validated_data.pop('client_birthday', None),
        }

        # Handle notifications
        telegram_user_id = validated_data.pop('telegram_user_id', None)
        send_telegram_notification = validated_data.pop('send_telegram_notification', True)
        send_sms_notification = validated_data.pop('send_sms_notification', True)

        # Determine lookup method - prefer phone, fallback to email
        client = None
        created = False

        if client_data['phone']:
            # Try to find client by phone first
            try:
                client = Client.objects.get(business=business, phone=client_data['phone'])
                created = False
                # Update client info if provided
                if client_data['name'] and client_data['name'] != client.name:
                    client.name = client_data['name']
                if client_data['email'] and client_data['email'] != client.email and not client.email.startswith('telegram_'):
                    # Don't overwrite telegram emails
                    client.email = client_data['email']
                if client_data['birthday'] and client_data['birthday'] != client.birthday:
                    client.birthday = client_data['birthday']
                client.save()
            except Client.DoesNotExist:
                # Check if there's already a Telegram user we should link to
                # Look for any client in this business with a telegram email that doesn't have a phone
                telegram_client = None
                try:
                    # Look for clients with telegram emails but no phone number
                    telegram_clients = Client.objects.filter(
                        business=business,
                        email__startswith='telegram_',
                        email__endswith='@fidelo.local',
                        phone__isnull=True
                    )
                    if telegram_clients.exists():
                        # For now, we can't automatically link without additional info
                        # Create a new client but log this for potential manual linking
                        pass
                except:
                    pass

                # Create new client with phone
                if not client_data['name']:
                    client_data['name'] = f"Cliente {client_data['phone']}"
                if not client_data['email']:
                    client_data['email'] = f"phone_{client_data['phone'].replace('+', '').replace(' ', '')}@fidelo.local"

                # Use ClientService to ensure loyalty account is created
                from .services import ClientService
                client = ClientService.create_client_with_account(business=business, **client_data)
                created = True
        elif client_data['email']:
            # Fallback to email lookup
            client, created = Client.objects.get_or_create(
                business=business,
                email=client_data['email'],
                defaults=client_data
            )
            # Ensure loyalty account exists for existing client
            if not created:
                from .models import LoyaltyAccount
                LoyaltyAccount.objects.get_or_create(
                    business=business,
                    client=client,
                    defaults={'points_balance': 0}
                )
        else:
            # Neither phone nor email provided
            raise serializers.ValidationError("Either client_phone or client_email must be provided")

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

        # Check if client has Telegram (either provided telegram_user_id or has telegram email)
        effective_telegram_user_id = telegram_user_id

        # Extract telegram user ID from client email if it's a telegram email
        if not effective_telegram_user_id and client.email.startswith('telegram_') and client.email.endswith('@fidelo.local'):
            effective_telegram_user_id = client.email.replace('telegram_', '').replace('@fidelo.local', '')

        # Send Telegram notification if enabled and we have a telegram user ID
        if send_telegram_notification and effective_telegram_user_id:
            try:
                from .telegram_notifications_sync import send_purchase_notification
                telegram_notification_sent = send_purchase_notification(
                    telegram_user_id=effective_telegram_user_id,
                    client_id=str(client.client_id),
                    purchase_id=str(purchase.purchase_id),
                    is_new_client=created
                )
            except Exception as e:
                # Log error but don't fail the purchase
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send Telegram notification: {e}")

        # Send SMS notification if enabled - TEMPORARILY DISABLED
        # SMS functionality disabled for first contact approach
        if False:  # send_sms_notification and client_data.get('phone'):
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