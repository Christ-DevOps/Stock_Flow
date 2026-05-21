import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
import django
django.setup()
from inventory.models import Product
low = [p for p in Product.objects.filter(status="active") if p.is_low_stock]
print(f"Active products: {Product.objects.filter(status='active').count()}")
print(f"Low stock: {len(low)}")
print("Stats:", [f"{p.name}: {p.quantity} (threshold={p.low_stock_threshold})" for p in low[:5]])
