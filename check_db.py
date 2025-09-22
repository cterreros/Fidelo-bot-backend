import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fidelo_backend.settings')
import django
django.setup()

from core.models import Business, Client, LoyaltyAccount, Purchase

print('=== ESTADO ACTUAL DE LA BASE DE DATOS ===')
print(f'Total negocios: {Business.objects.count()}')
print(f'Total clientes: {Client.objects.count()}')
print(f'Total compras: {Purchase.objects.count()}')
print(f'Total cuentas lealtad: {LoyaltyAccount.objects.count()}')

print('\n=== DETALLES DE NEGOCIOS ===')
for business in Business.objects.all():
    print(f'- {business.name}')
    print(f'  ID: {business.business_id}')
    print(f'  Activo: {business.is_active}')

print('\n=== DETALLES DE CLIENTES ===')
if Client.objects.exists():
    for client in Client.objects.all():
        print(f'- {client.name}')
        print(f'  Email: {client.email}')
        print(f'  Teléfono: {client.phone}')
        print(f'  Negocio: {client.business.name}')
        print(f'  ID Cliente: {client.client_id}')
        print()
else:
    print('No hay clientes registrados')

print('\n=== DETALLES DE COMPRAS ===')
if Purchase.objects.exists():
    for purchase in Purchase.objects.all():
        print(f'- ${purchase.amount} {purchase.currency}')
        print(f'  Cliente: {purchase.client.name}')
        print(f'  Teléfono cliente: {purchase.client.phone}')
        print(f'  Negocio: {purchase.business.name}')
        print(f'  Fecha: {purchase.purchased_at}')
        print()
else:
    print('No hay compras registradas')