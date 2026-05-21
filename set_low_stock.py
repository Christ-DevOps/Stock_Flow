import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
import django
django.setup()
from inventory.models import Product
for p in list(Product.objects.all())[:6]:
    p.quantity = p.low_stock_threshold - 1
    p.save()
    print(f"Set '{p.name}' qty={p.quantity} threshold={p.low_stock_threshold} low={p.is_low_stock}")
print("Done.")
