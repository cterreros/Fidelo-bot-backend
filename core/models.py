import uuid
from django.db import models
from django.utils import timezone


class Business(models.Model):
    business_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    email = models.EmailField()
    timezone = models.CharField(max_length=64, default="America/Mexico_City")
    points_per_currency = models.DecimalField(max_digits=6, decimal_places=3, default=0.1)
    birthday_bonus_points = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"


class Client(models.Model):
    client_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    joined_at = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    class Meta:
        unique_together = (("business", "email"), ("business", "phone"))
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class LoyaltyAccount(models.Model):
    account_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    points_balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.points_balance} points"

    class Meta:
        verbose_name = "Loyalty Account"
        verbose_name_plural = "Loyalty Accounts"


class Purchase(models.Model):
    purchase_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="MXN")
    purchased_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.name} - ${self.amount} {self.currency}"

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchased_at']


class PointEvent(models.Model):
    class Source(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        BIRTHDAY = "birthday", "Birthday"
        ADJUSTMENT = "adjustment", "Adjustment"

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source = models.CharField(max_length=16, choices=Source.choices)
    points = models.IntegerField()
    related_purchase = models.ForeignKey(Purchase, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=200, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sign = "+" if self.points > 0 else ""
        return f"{self.client.name} - {sign}{self.points} pts ({self.get_source_display()})"

    class Meta:
        verbose_name = "Point Event"
        verbose_name_plural = "Point Events"
        ordering = ['-occurred_at']
