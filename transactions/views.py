from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from catalog.models import Product
from .forms import CustomerForm
from .models import Customer, Sale, SaleItem

def cart_products(request):
    ids = request.session.get('cart', [])
    return Product.objects.filter(id__in=ids, sold=False).select_related('category', 'supplier')

def cart_context(request):
    products = cart_products(request)
    return {'products': products, 'total': sum((p.listed_price for p in products), Decimal('0'))}

def cart_partial(request):
    return render(request, 'transactions/partials/cart.html', cart_context(request))

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, sold=False)
    cart = request.session.setdefault('cart', [])
    if product.id not in cart:
        cart.append(product.id)
        request.session.modified = True
    if request.headers.get('HX-Request'):
        return cart_partial(request)
    return redirect('catalog:shop')

@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', [])
    if product_id in cart:
        cart.remove(product_id)
        request.session.modified = True
    if request.headers.get('HX-Request'):
        return cart_partial(request)
    return redirect(request.META.get('HTTP_REFERER', 'transactions:checkout'))

def checkout(request):
    context = cart_context(request)
    products, total = context['products'], context['total']
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid() and products.exists():
            with transaction.atomic():
                locked_products = list(Product.objects.select_for_update().filter(
                    id__in=products.values_list('id', flat=True), sold=False, sale_items__isnull=True
                ))
                if len(locked_products) != products.count():
                    messages.error(request, 'One or more items are no longer available. Please review your cart.')
                    return redirect('transactions:checkout')
                customer = form.save()
                sale = Sale.objects.create(customer=customer, total=total, payment_reference='FAKE-PIX-DEVELOPMENT')
                for product in locked_products:
                    SaleItem.objects.create(sale=sale, product=product, price=product.listed_price, supplier_rate=product.supplier_share_rate(timezone.localdate()))
            request.session['cart'] = []
            request.session['sale_id'] = sale.id
            return redirect('transactions:complete')
    else:
        form = CustomerForm()
    return render(request, 'transactions/checkout.html', {**context, 'form': form})

def complete(request):
    sale_id = request.session.get('sale_id')
    if not sale_id:
        return redirect('catalog:home')
    sale = get_object_or_404(Sale, pk=sale_id)
    return render(request, 'transactions/complete.html', {'sale': sale})

@require_POST
def simulate_payment(request):
    sale_id = request.session.get('sale_id')
    if not sale_id:
        return redirect('catalog:home')
    sale = get_object_or_404(Sale, pk=sale_id, status='pending')
    sale.mark_paid()
    messages.success(request, 'Payment approved. Your receipt has been sent by email.')
    return redirect('transactions:complete')
