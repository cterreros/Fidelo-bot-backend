#!/usr/bin/env python3
"""
Script para diagnosticar el registro de usuario y notificaciones
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from core.models import Client, Business, Purchase, LoyaltyAccount
from django.conf import settings


def debug_user_registration():
    """Diagnosticar el registro de usuario más reciente"""
    print("========================================")
    print("      DIAGNOSTICO DE USUARIO")
    print("========================================")

    # 1. Verificar configuración de Telegram
    print("\n1. CONFIGURACIÓN DE TELEGRAM:")
    print(f"   Token configurado: {'SÍ' if settings.TELEGRAM_BOT_TOKEN else 'NO'}")
    if settings.TELEGRAM_BOT_TOKEN:
        print(f"   Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...{settings.TELEGRAM_BOT_TOKEN[-10:]}")

    # 2. Buscar el cliente más reciente
    print("\n2. CLIENTE MÁS RECIENTE:")
    try:
        latest_client = Client.objects.order_by('-created_at').first()
        if not latest_client:
            print("   ERROR: No se encontraron clientes")
            return False

        print(f"   Nombre: {latest_client.name}")
        print(f"   Email: {latest_client.email}")
        print(f"   Teléfono: {latest_client.phone}")
        print(f"   Cumpleaños: {latest_client.birthday}")
        print(f"   Negocio: {latest_client.business.name}")
        print(f"   Creado: {latest_client.created_at}")

        # Verificar si el email contiene telegram_user_id
        if 'telegram_' in latest_client.email and '@fidelo.local' in latest_client.email:
            telegram_id = latest_client.email.replace('telegram_', '').replace('@fidelo.local', '')
            print(f"   Telegram ID detectado: {telegram_id}")
        else:
            print(f"   PROBLEMA: Email no tiene formato Telegram: {latest_client.email}")

    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    # 3. Verificar compras del cliente
    print("\n3. COMPRAS DEL CLIENTE:")
    try:
        purchases = Purchase.objects.filter(client=latest_client).order_by('-created_at')
        print(f"   Total compras: {purchases.count()}")

        for i, purchase in enumerate(purchases[:3], 1):
            points_earned = int(purchase.amount * latest_client.business.points_per_currency)
            print(f"   Compra {i}:")
            print(f"      Monto: ${purchase.amount}")
            print(f"      Moneda: {purchase.currency}")
            print(f"      Puntos ganados: {points_earned}")
            print(f"      Fecha: {purchase.created_at}")

    except Exception as e:
        print(f"   ERROR: {e}")

    # 4. Verificar cuenta de lealtad
    print("\n4. CUENTA DE LEALTAD:")
    try:
        account = LoyaltyAccount.objects.get(client=latest_client)
        print(f"   Balance actual: {account.points_balance}")
        print(f"   Última actualización: {account.updated_at}")
    except LoyaltyAccount.DoesNotExist:
        print("   ERROR: No se encontró cuenta de lealtad")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 5. Verificar los logs del servidor
    print("\n5. ANÁLISIS DEL PROBLEMA:")
    print("   Posibles causas por las que no llegó la notificación:")
    print("   a) El telegram_user_id no está en formato correcto")
    print("   b) No has iniciado conversación con el bot")
    print("   c) El bot de Telegram no está funcionando")
    print("   d) Error en el envío de la notificación")

    return True


def test_notification_manually():
    """Probar notificación manualmente"""
    print("\n========================================")
    print("      PRUEBA MANUAL DE NOTIFICACIÓN")
    print("========================================")

    try:
        latest_client = Client.objects.order_by('-created_at').first()
        latest_purchase = Purchase.objects.filter(client=latest_client).order_by('-created_at').first()

        if not latest_client or not latest_purchase:
            print("ERROR: No se encontraron datos")
            return False

        # Pedir telegram_user_id real
        print(f"\nCliente: {latest_client.name}")
        print(f"Email registrado: {latest_client.email}")

        telegram_id = input("Ingresa tu Telegram User ID real (número): ").strip()

        if not telegram_id.isdigit():
            print("ERROR: El Telegram ID debe ser un número")
            return False

        print(f"\nIntentando enviar notificación a Telegram ID: {telegram_id}")

        # Importar y usar la función de notificación
        from core.telegram_notifications import send_purchase_notification

        success = send_purchase_notification(
            telegram_user_id=telegram_id,
            client_id=str(latest_client.client_id),
            purchase_id=str(latest_purchase.purchase_id),
            is_new_client=True
        )

        if success:
            print("✅ SUCCESS: Notificación enviada!")
            print("Revisa tu Telegram")

            # Actualizar el email del cliente para futuras notificaciones automáticas
            latest_client.email = f"telegram_{telegram_id}@fidelo.local"
            latest_client.save()
            print(f"✅ Email actualizado para futuras notificaciones: {latest_client.email}")

        else:
            print("❌ ERROR: No se pudo enviar la notificación")
            print("\nPosibles soluciones:")
            print("1. Busca tu bot en Telegram usando el token")
            print("2. Inicia conversación con /start")
            print("3. Verifica que el Telegram ID sea correcto")

        return success

    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    print("DIAGNÓSTICO DEL SISTEMA DE NOTIFICACIONES")
    print("1. Ver diagnóstico completo")
    print("2. Probar notificación manual")

    choice = input("\nSelecciona opción (1 o 2): ").strip()

    if choice == "1":
        debug_user_registration()
    elif choice == "2":
        test_notification_manually()
    else:
        debug_user_registration()

    print("\n" + "="*50)
    print("PARA OBTENER TU TELEGRAM ID:")
    print("1. Abre Telegram")
    print("2. Busca @userinfobot")
    print("3. Envía /start")
    print("4. Te dará tu User ID (ejemplo: 123456789)")
    print("="*50)