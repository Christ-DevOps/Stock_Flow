from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Product, Category, Supplier, ProductVariant, StockMovement, PurchaseOrder


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "parent"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "parent": forms.Select(attrs={"class": "form-select"}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "email", "phone", "address", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "category", "supplier", "description",
            "sku", "barcode",
            "price", "cost_price",
            "quantity", "unit",
            "low_stock_threshold", "max_stock_threshold",
            "image", "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. SKU-001"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "cost_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "max_stock_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["variant_name", "variant_value", "sku", "barcode", "price", "quantity"]
        widgets = {
            "variant_name": forms.TextInput(attrs={"class": "form-control"}),
            "variant_value": forms.TextInput(attrs={"class": "form-control"}),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "barcode": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ["product", "movement_type", "quantity", "reason", "notes"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "movement_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "reason": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("quantity")
        mtype = cleaned.get("movement_type")
        if qty and qty <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return cleaned

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return qty


class StockMovementQuickForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status="active"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    movement_type = forms.ChoiceField(
        choices=StockMovement.MOVEMENT_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.IntegerField(
        min_value=1, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Qty"}),
    )
    reason = forms.ChoiceField(
        choices=StockMovement.REASON_CODES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Notes…"}),
    )


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "product", "quantity", "unit_price", "expected_date", "notes"]
        widgets = {
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "product": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "expected_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("quantity")
        price = cleaned.get("unit_price")
        if qty and price:
            cleaned["total_amount"] = qty * price
        return cleaned
