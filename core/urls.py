from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessViewSet, ClientViewSet, LoyaltyAccountViewSet,
    PurchaseViewSet, PointEventViewSet, PurchaseWithClientDataView,
    purchase_form_view
)

router = DefaultRouter()
router.register(r'businesses', BusinessViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'loyalty-accounts', LoyaltyAccountViewSet)
router.register(r'purchases', PurchaseViewSet)
router.register(r'point-events', PointEventViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Special endpoint for POS integration
    path('purchase-with-client/', PurchaseWithClientDataView.as_view(), name='purchase-with-client'),
    # Web form for manual purchase registration
    path('purchase-form/', purchase_form_view, name='purchase-form'),
]