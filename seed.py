import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Role, SystemSettings, AuditLog

U = get_user_model()

# Create manager user
manager, created = U.objects.get_or_create(
    username="manager1",
    defaults={"is_staff": True, "first_name": "John", "last_name": "Smith", "email": "manager@stockpro.local"}
)
manager.set_password("manager123")
manager.save()

mgr_role, _ = Role.objects.get_or_create(name="Manager")
admin_role, _ = Role.objects.get_or_create(name="Admin")
manager.profile.role = mgr_role
manager.profile.save()

# Seed SystemSettings
settings = SystemSettings.get_settings()

print("=== Sample Users ===")
print(f"Admin      : admin        / admin123")
print(f"Manager    : manager1     / manager123")
print(f"Roles      : {Role.objects.count()} ({', '.join(R.name for R in Role.objects.all())})")
print(f"Settings   : store_name={settings.store_name}")
print("Seeding complete!")
