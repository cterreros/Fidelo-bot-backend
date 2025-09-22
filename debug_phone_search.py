import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
import django
django.setup()

from core.models import Business, Client

# El teléfono que estás usando
test_phone = "+529511577551"
print(f"Buscando teléfono: '{test_phone}'")

# Ver todos los negocios
print("\n=== TODOS LOS NEGOCIOS ===")
for business in Business.objects.all():
    print(f"- {business.name}")
    print(f"  ID: {business.business_id}")

    # Buscar cliente en este negocio con el teléfono
    try:
        client = Client.objects.get(business=business, phone=test_phone)
        print(f"  SI CLIENTE ENCONTRADO: {client.name}")
        print(f"     Email: {client.email}")
        print(f"     Telefono: '{client.phone}'")
    except Client.DoesNotExist:
        print(f"  NO Cliente NO encontrado con telefono {test_phone}")
    print()

# Verificar el cliente registrado
print("=== CLIENTE REGISTRADO ===")
client = Client.objects.first()
if client:
    print(f"Nombre: {client.name}")
    print(f"Teléfono guardado: '{client.phone}'")
    print(f"Teléfono buscado:   '{test_phone}'")
    print(f"¿Son iguales? {client.phone == test_phone}")
    print(f"Negocio: {client.business.name}")
    print(f"Business ID: {client.business.business_id}")
else:
    print("No hay cliente registrado")