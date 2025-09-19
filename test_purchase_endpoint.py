#!/usr/bin/env python3
"""
Script para probar el endpoint purchase-with-client y diagnosticar errores
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
django.setup()

from django.test import Client as TestClient


def test_purchase_endpoint():
    """Probar el endpoint purchase-with-client con diferentes datos"""
    print("========================================")
    print("      TESTING PURCHASE-WITH-CLIENT")
    print("========================================")

    client = TestClient()

    # Datos de prueba
    test_data = {
        "business_id": "fdf5c40f-4139-4074-8efe-bce7ab8eb725",
        "amount": "100.00",
        "currency": "MXN",
        "client_name": "Test User",
        "client_email": "test@example.com",
        "client_phone": "+521234567890",
        "client_birthday": "1990-01-01",
        "telegram_user_id": "1384969740",
        "send_telegram_notification": True
    }

    print("\n1. DATOS DE PRUEBA:")
    print(json.dumps(test_data, indent=2))

    # Verificar que el business existe
    print("\n2. VERIFICANDO BUSINESS:")
    try:
        from core.models import Business
        business = Business.objects.get(business_id=test_data["business_id"])
        print(f"   ✅ Business encontrado: {business.name}")
    except Business.DoesNotExist:
        print("   ❌ ERROR: Business no existe")

        # Mostrar businesses disponibles
        businesses = Business.objects.all()
        print("   Businesses disponibles:")
        for b in businesses:
            print(f"     - {b.business_id}: {b.name}")

        if businesses:
            # Usar el primer business
            business = businesses.first()
            test_data["business_id"] = str(business.business_id)
            print(f"   🔄 Usando business: {business.name}")
        else:
            print("   ❌ No hay businesses disponibles")
            return False

    # Probar el endpoint
    print("\n3. PROBANDO ENDPOINT:")
    response = client.post(
        '/api/purchase-with-client/',
        data=json.dumps(test_data),
        content_type='application/json'
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200 or response.status_code == 201:
        print("   ✅ SUCCESS!")
        result = response.json()
        print(f"   Purchase ID: {result.get('purchase_id', 'N/A')}")
        print(f"   Client ID: {result.get('client_id', 'N/A')}")
        print(f"   New client: {result.get('created_new_client', 'N/A')}")
        print(f"   Telegram sent: {result.get('telegram_notification_sent', 'N/A')}")
        return True
    else:
        print("   ❌ ERROR!")
        try:
            error_data = response.json()
            print("   Detalles del error:")
            print(json.dumps(error_data, indent=4))
        except:
            print(f"   Response content: {response.content}")
        return False


def show_available_data():
    """Mostrar datos disponibles en la BD"""
    print("\n========================================")
    print("           DATOS DISPONIBLES")
    print("========================================")

    try:
        from core.models import Business, Client

        # Mostrar businesses
        businesses = Business.objects.all()
        print(f"\n📊 BUSINESSES ({businesses.count()}):")
        for b in businesses:
            print(f"   - ID: {b.business_id}")
            print(f"     Nombre: {b.name}")
            print(f"     Email: {b.email}")
            print(f"     Puntos por peso: {b.points_per_currency}")
            print()

        # Mostrar clientes
        clients = Client.objects.all()
        print(f"👥 CLIENTS ({clients.count()}):")
        for c in clients:
            print(f"   - ID: {c.client_id}")
            print(f"     Nombre: {c.name}")
            print(f"     Email: {c.email}")
            print(f"     Business: {c.business.name}")
            print()

    except Exception as e:
        print(f"Error mostrando datos: {e}")


if __name__ == "__main__":
    print("¿Qué quieres hacer?")
    print("1. Probar endpoint purchase-with-client")
    print("2. Ver datos disponibles en BD")
    print("3. Ambos")

    choice = input("Selecciona (1, 2 o 3): ").strip()

    if choice == "1":
        test_purchase_endpoint()
    elif choice == "2":
        show_available_data()
    elif choice == "3":
        show_available_data()
        test_purchase_endpoint()
    else:
        print("Opción inválida")
        sys.exit(1)