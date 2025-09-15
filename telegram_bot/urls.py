from django.urls import path
from . import views

app_name = 'telegram_bot'

urlpatterns = [
    path('webhook/', views.TelegramWebhookView.as_view(), name='webhook'),
    path('webhook/info/', views.webhook_info, name='webhook_info'),
    path('webhook/set/', views.set_webhook, name='set_webhook'),
    path('webhook/delete/', views.delete_webhook, name='delete_webhook'),
    path('bot/info/', views.bot_info, name='bot_info'),
]