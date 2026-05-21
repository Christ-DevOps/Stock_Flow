import os, sys, random
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
import django
django.setup()

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from inventory.models import Category, Supplier, Product, StockMovement, PurchaseOrder, Notification

now = timezone.now()

# --- Categories ---
cats_data = [
    ("Electronics", "Smartphones, tablets, accessories"),
    ("Clothing", "Apparel and fashion wearables"),
    ("Groceries", "Food and beverage items"),
    ("Home & Garden", "Tools, furniture, plants"),
    ("Sports", "Sports equipment and gear"),
    ("Toys", "Games, toys, and hobbies"),
]
categories = {}
for name, desc in cats_data:
    c, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
    categories[name] = c

# --- Suppliers ---
sups_data = [
    ("TechHub Ltd", "Alice Johnson", "alice@techhub.com", "+1-555-0101", "123 Silicon Ave"),
    ("StyleCo", "Bob Williams", "bob@styleco.com", "+1-555-0102", "456 Fashion St"),
    ("FreshFoods Inc", "Carol Brown", "carol@freshfoods.com", "+1-555-0103", "789 Market Rd"),
    ("GreenThumb", "David Lee", "david@greenthumb.com", "+1-555-0104", "321 Garden Ln"),
]
suppliers = {}
for name, contact, email, phone, addr in sups_data:
    s, _ = Supplier.objects.get_or_create(
        name=name,
        defaults={"contact_person": contact, "email": email, "phone": phone, "address": addr},
    )
    suppliers[name] = s

# --- Products ---
prods_data = [
    # (name, cat, sup, sku, barcode, cost, price, qty, unit, low, max)
    ("iPhone 15 Pro",                    "Electronics", "TechHub Ltd",        "ELEC-001", "890123456700",  999.00, 1199.00, 25,  "piece", 5,   100),
    ("Samsung Galaxy S24",               "Electronics", "TechHub Ltd",        "ELEC-002", "890123456701",  799.00,  999.00, 18,  "piece", 5,   100),
    ("Wireless Earbuds",                 "Electronics", "TechHub Ltd",        "ELEC-003", "890123456702",  49.00,   79.00, 150,  "piece", 20,  500),
    ("USB-C Charger 65W",                "Electronics", "TechHub Ltd",        "ELEC-004", "890123456703",  19.00,   34.99, 200,  "piece", 30,  800),
    ("Laptop Stand",                     "Electronics", "TechHub Ltd",        "ELEC-005", "890123456704",  35.00,   59.00, 60,   "piece", 10,  200),
    ("Cotton T-Shirt",                   "Clothing",    "StyleCo",            "CLO-001",  "890123456710",   8.00,   19.99, 300,  "piece", 50, 1000),
    ("Denim Jeans",                      "Clothing",    "StyleCo",            "CLO-002",  "890123456711",  25.00,   59.99, 120,  "piece", 25,  400),
    ("Winter Jacket",                    "Clothing",    "StyleCo",            "CLO-003",  "890123456712",  55.00,  129.99, 45,   "piece", 10,  150),
    ("Running Shoes",                    "Clothing",    "StyleCo",            "CLO-004",  "890123456713",  40.00,   89.99, 80,   "pair",  15,  300),
    ("Organic Rice 5kg",                 "Groceries",   "FreshFoods Inc",     "GRO-001",  "890123456720",   7.50,   14.99, 500,  "pack", 100, 1500),
    ("Olive Oil 1L",                     "Groceries",   "FreshFoods Inc",     "GRO-002",  "890123456721",   6.00,   12.99, 350,  "piece",  80,  800),
    ("Cereal Box 500g",                  "Groceries",   "FreshFoods Inc",     "GRO-003",  "890123456722",   3.50,    7.99, 600,  "piece", 150, 2000),
    ("Bamboo Plant Pot",                 "Home & Garden","GreenThumb",        "HOM-001",  "890123456730",  12.00,   27.99, 90,   "piece", 15,  300),
    ("LED Desk Lamp",                    "Home & Garden","GreenThumb",        "HOM-002",  "890123456731",  22.00,   44.99, 70,   "piece", 10,  200),
    ("Yoga Mat",                         "Sports",      "GreenThumb",         "SPO-001",  "890123456740",  18.00,   39.99, 110,  "piece", 20,  300),
    ("Basketball",                       "Sports",      "GreenThumb",         "SPO-002",  "890123456741",  15.00,   29.99, 85,   "piece", 15,  250),
    ("LEGO Classic Set",                 "Toys",        "TechHub Ltd",        "TOY-001",  "890123456750",  40.00,   79.99, 55,   "set",    8,   150),
    ("Board Game - Strategy",            "Toys",        "StyleCo",            "TOY-002",  "890123456751",  20.00,   45.00, 70,   "piece", 12,  180),
]

products = []
for name, cat_name, sup_name, sku, barcode, cost, price, qty, unit, low, max_ in prods_data:
    p, _ = Product.objects.get_or_create(
        sku=sku,
        defaults=dict(
            name=name,
            category=categories[cat_name],
            supplier=suppliers[sup_name],
            sku=sku,
            barcode=barcode,
            cost_price=Decimal(str(cost)),
            price=Decimal(str(price)),
            quantity=qty,
            unit=unit,
            low_stock_threshold=low,
            max_stock_threshold=max_,
        ),
    )
    products.append(p)

print(f"Products created: {Product.objects.count()}")

# --- Stock Movements (last 30 days) ---
mvmt_types_reasons = [
    ("IN",  "delivery"),
    ("OUT", "sale"),
    ("OUT", "sale"),
    ("RETURN_IN", "return_customer"),
    ("ADJUST", "inventory_count"),
]
for i in range(60):
    p = random.choice(products)
    mtype, reason = random.choice(mvmt_types_reasons)
    qty = random.randint(1, 10)
    if mtype == "OUT" and p.quantity < qty:
        qty = 1
    date = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 20))
    created = not StockMovement.objects.filter(product=p, movement_type=mtype, reason=reason, date=date).exists()
    if created:
        StockMovement.objects.create(
            product=p, movement_type=mtype, quantity=qty, reason=reason,
            notes=f"Auto-generated sample {mtype} movement",
            date=date, recorded_by="manager1",
        )

print(f"Stock movements created: {StockMovement.objects.count()}")

# --- Purchase Orders ---
from inventory.models import PurchaseOrder
for p in random.sample(products, 6):
    po, _ = PurchaseOrder.objects.get_or_create(
        order_number=f"PO-SAMPLE-{p.sku[-4:]}",
        defaults=dict(
            supplier=p.supplier,
            product=p,
            quantity=random.randint(50, 200),
            unit_price=p.cost_price,
            status=random.choice(["draft", "sent", "received"]),
            expected_date=now.date() + timedelta(days=random.randint(3, 14)),
        ),
    )

print(f"Purchase orders: {PurchaseOrder.objects.count()}")

# --- Notifications ---
low_stock_prods = [p for p in Product.objects.filter(status="active") if p.is_low_stock]
for p in low_stock_prods[:5]:
    Notification.objects.get_or_create(
        notification_type="low_stock",
        title=f"Low Stock: {p.name}",
        message=f"{p.name} has only {p.quantity} units remaining (threshold: {p.low_stock_threshold}).",
        product=p,
        defaults={"is_read": False},
    )

print(f"Low stock notifications: {Notification.objects.filter(notification_type='low_stock').count()}")
print("\nSample data seeding complete!")
