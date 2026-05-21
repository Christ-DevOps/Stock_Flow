from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.filter(status="active").count()

    @property
    def total_value(self):
        total = Decimal("0")
        for p in self.products.filter(status="active"):
            total += p.total_value
        return total


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
    ]
    UNIT_CHOICES = [
        ("piece", "Piece"),
        ("kg", "Kilogram"),
        ("g", "Gram"),
        ("l", "Liter"),
        ("ml", "Milliliter"),
        ("box", "Box"),
        ("pack", "Pack"),
        ("set", "Set"),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="piece")
    low_stock_threshold = models.IntegerField(default=10)
    max_stock_threshold = models.IntegerField(default=1000)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "quantity"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        return self.name

    @property
    def stock_status(self):
        if self.quantity <= self.low_stock_threshold:
            return "low"
        if self.quantity >= self.max_stock_threshold:
            return "overstock"
        return "ok"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def is_overstock(self):
        return self.quantity >= self.max_stock_threshold

    @property
    def total_value(self):
        return self.cost_price * self.quantity

    @property
    def margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price * 100).quantize(Decimal("0.01"))
        return Decimal("0.00")


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    variant_name = models.CharField(max_length=100)
    variant_value = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ["product", "variant_name", "variant_value"]

    def __str__(self):
        return f"{self.product.name} - {self.variant_value}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("ADJUST", "Adjustment"),
        ("RETURN_IN", "Return In"),
        ("RETURN_OUT", "Return Out"),
    ]
    REASON_CODES = [
        ("delivery", "New Delivery"),
        ("restock", "Restocking"),
        ("sale", "Sale"),
        ("damage", "Damage"),
        ("write_off", "Write-off"),
        ("return_customer", "Customer Return"),
        ("return_supplier", "Return to Supplier"),
        ("inventory_count", "Inventory Count"),
        ("other", "Other"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=50, choices=REASON_CODES)
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["product", "-date"])]

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase_orders")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_date = models.DateField(blank=True, null=True)
    received_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone
            self.order_number = f"PO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        if not self.total_amount:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("low_stock", "Low Stock"),
        ("overstock", "Overstock"),
        ("order_received", "Order Received"),
        ("stock_movement", "Stock Movement"),
        ("system", "System"),
    ]
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
