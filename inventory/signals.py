from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Product, StockMovement, Notification, PurchaseOrder


@receiver([post_save, post_delete], sender=StockMovement)
def update_product_stock(sender, instance, **kwargs):
    if not transaction.get_connection().in_atomic_block:
        product = Product.objects.select_for_update().get(pk=instance.product_id)
        if instance.movement_type in ("IN", "RETURN_IN"):
            product.quantity += instance.quantity
        else:
            product.quantity = max(0, product.quantity - instance.quantity)
        product.save(update_fields=["quantity"])


@receiver(post_save, sender=StockMovement)
def generate_movement_alert(sender, instance, created, **kwargs):
    Notification.objects.get_or_create(
        product_id=instance.product_id,
        notification_type="stock_movement",
        title=f"Stock movement: {instance.product.name}",
        defaults={"message": f"{instance.movement_type} — {instance.quantity} units ({instance.reason})"},
    )
