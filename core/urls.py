from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessViewSet, ClientViewSet, LoyaltyAccountViewSet,
    PurchaseViewSet, PointEventViewSet
)

router = DefaultRouter()
router.register(r'businesses', BusinessViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'loyalty-accounts', LoyaltyAccountViewSet)
router.register(r'purchases', PurchaseViewSet)
router.register(r'point-events', PointEventViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]