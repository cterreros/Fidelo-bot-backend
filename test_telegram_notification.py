#!/usr/bin/env python3
"""
Test script para probar notificaciones de Telegram manualmente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from core.telegram_notifications import send_purchase_notification
from core.models import Client, Purchase


def test_manual_notification():
    """Probar notificación manual"""
    print("========================================")
    print("      TESTING TELEGRAM NOTIFICATION")
    print("========================================")

    # Buscar el último cliente creado
    try:
        latest_client = Client.objects.order_by('-created_at').first()
        if not latest_client:
            print("ERROR: No se encontraron clientes")
            return False

        print(f"Cliente encontrado: {latest_client.name}")
        print(f"Email: {latest_client.email}")
        print(f"Negocio: {latest_client.business.name}")

        # Buscar la última compra de este cliente
        latest_purchase = Purchase.objects.filter(client=latest_client).order_by('-created_at').first()
        if not latest_purchase:
            print("ERROR: No se encontraron compras para este cliente")
            return False

        print(f"Compra encontrada: ${latest_purchase.amount}")

        # Extraer telegram_user_id del email si es formato telegram_
        telegram_user_id = None
        if latest_client.email.startswith('telegram_') and latest_client.email.endswith('@fidelo.local'):
            telegram_user_id = latest_client.email.replace('telegram_', '').replace('@fidelo.local', '')
            print(f"Telegram ID extraído del email: {telegram_user_id}")
        else:
            # Si no es formato telegram_, pedir el ID
            print(f"El cliente no tiene formato telegram en email: {latest_client.email}")
            telegram_user_id = input("Ingresa tu Telegram User ID: ").strip()

        if not telegram_user_id:
            print("ERROR: No se proporcionó Telegram User ID")
            return False

        print(f"\nEnviando notificación a Telegram ID: {telegram_user_id}")

        # Enviar notificación
        success = send_purchase_notification(
            telegram_user_id=telegram_user_id,
            client_id=str(latest_client.client_id),
            purchase_id=str(latest_purchase.purchase_id),
            is_new_client=True
        )

        if success:
            print("SUCCESS: Notificación enviada correctamente!")
            print("Revisa tu Telegram para ver el mensaje")
        else:
            print("ERROR: No se pudo enviar la notificación")
            print("Posibles causas:")
            print("1. El Telegram ID es incorrecto")
            print("2. No has iniciado conversación con el bot")
            print("3. El bot no está corriendo")

        return success

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def get_telegram_id_instructions():
    """Mostrar instrucciones para obtener Telegram ID"""
    print("\n========================================")
    print("    COMO OBTENER TU TELEGRAM ID")
    print("========================================")
    print("\n1. Abre Telegram")
    print("2. Busca el bot: @userinfobot")
    print("3. Envía /start")
    print("4. Te dará tu User ID (ejemplo: 123456789)")
    print("5. Ese número es tu telegram_user_id")
    print("\nAlternativamente:")
    print("1. Busca: @FideloBot_Bot (o como se llame tu bot)")
    print("2. Envía /start")
    print("3. Usa /notifications para probar")


if __name__ == "__main__":
    print("¿Qué quieres hacer?")
    print("1. Probar notificación manual")
    print("2. Ver instrucciones para obtener Telegram ID")

    choice = input("Selecciona (1 o 2): ").strip()

    if choice == "1":
        success = test_manual_notification()
        if not success:
            sys.exit(1)
    elif choice == "2":
        get_telegram_id_instructions()
    else:
        print("Opción inválida")
        sys.exit(1)