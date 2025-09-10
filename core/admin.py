from django.contrib import admin
from .models import Business, Client, LoyaltyAccount, Purchase, PointEvent


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'points_per_currency', 'birthday_bonus_points', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('business_id', 'created_at', 'updated_at')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'email', 'phone', 'birthday', 'joined_at')
    list_filter = ('business', 'joined_at', 'birthday')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('client_id', 'created_at', 'updated_at')


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('client', 'business', 'points_balance', 'updated_at')
    list_filter = ('business', 'updated_at')
    search_fields = ('client__name', 'client__email')
    readonly_fields = ('account_id', 'updated_at')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('client', 'business', 'amount', 'currency', 'purchased_at')
    list_filter = ('business', 'currency', 'purchased_at')
    search_fields = ('client__name', 'client__email')
    readonly_fields = ('purchase_id', 'created_at')
    date_hierarchy = 'purchased_at'


@admin.register(PointEvent)
class PointEventAdmin(admin.ModelAdmin):
    list_display = ('client', 'business', 'source', 'points', 'related_purchase', 'occurred_at')
    list_filter = ('business', 'source', 'occurred_at')
    search_fields = ('client__name', 'client__email', 'note')
    readonly_fields = ('event_id', 'created_at')
    date_hierarchy = 'occurred_at'
