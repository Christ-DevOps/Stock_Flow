from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockMovementForm


# ============================================================
# DASHBOARD — the homepage showing summary info
# ============================================================
def dashboard(request):
    products = Product.objects.all()
    low_stock_products = [p for p in products if p.is_low_stock()]
    total_value = sum(p.total_value() for p in products)
    recent_movements = StockMovement.objects.order_by('-date')[:10]

    context = {
        'total_products': products.count(),
        'low_stock_count': len(low_stock_products),
        'low_stock_products': low_stock_products,
        'total_value': total_value,
        'recent_movements': recent_movements,
    }
    return render(request, 'inventory/dashboard.html', context)


# ============================================================
# PRODUCT LIST — shows all products with search & filter
# ============================================================
def product_list(request):
    query = request.GET.get('q', '')          # Grab ?q=... from the URL if present
    category_id = request.GET.get('category', '')

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)  # Search by name

    if category_id:
        products = products.filter(category__id=category_id)

    categories = Category.objects.all()
    return render(request, 'inventory/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query,
    })


# ============================================================
# PRODUCT DETAIL — one product + its full stock history
# ============================================================
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.movements.order_by('-date')
    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'movements': movements,
    })


# ============================================================
# CREATE PRODUCT
# ============================================================
def product_create(request):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('product_list')
    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Add New Product'
    })


# ============================================================
# EDIT PRODUCT
# ============================================================
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(instance=product)      # Pre-fills the form with existing data
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_detail', pk=pk)
    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Edit Product'
    })


# ============================================================
# DELETE PRODUCT
# ============================================================
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':              # Only delete on form POST, not GET
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {
        'product': product
    })


# ============================================================
# ADD STOCK
# ============================================================
def stock_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockMovementForm()

    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            product.quantity += qty           # Increase the stock number
            product.save()

            StockMovement.objects.create(     # Log this movement in the database
                product=product,
                movement_type='IN',
                quantity=qty,
                reason=reason,
            )
            messages.success(request, f'{qty} units added to {product.name}.')
            return redirect('product_detail', pk=pk)

    return render(request, 'inventory/stock_form.html', {
        'form': form,
        'product': product,
        'action': 'Add Stock'
    })


# ============================================================
# REMOVE STOCK
# ============================================================
def stock_remove(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockMovementForm()

    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            if qty > product.quantity:        # Safety check — can't go below 0
                messages.error(request, f'Not enough stock! Only {product.quantity} units available.')
            else:
                product.quantity -= qty
                product.save()

                StockMovement.objects.create(
                    product=product,
                    movement_type='OUT',
                    quantity=qty,
                    reason=reason,
                )
                messages.success(request, f'{qty} units removed from {product.name}.')
                return redirect('product_detail', pk=pk)

    return render(request, 'inventory/stock_form.html', {
        'form': form,
        'product': product,
        'action': 'Remove Stock'
    })


# ============================================================
# CATEGORIES
# ============================================================
def category_list(request):
    categories = Category.objects.all()
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added!')
            return redirect('category_list')

    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'form': form
    })
