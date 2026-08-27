from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SupplierRegistrationForm
from .models import Supplier


def register(request):
    if request.method == 'POST':
        form = SupplierRegistrationForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            supplier.send_statement_email()
            request.session['registered_supplier_name'] = supplier.name
            messages.success(request, 'Your supplier registration was completed successfully.')
            return redirect('suppliers:registration_complete')
    else:
        form = SupplierRegistrationForm()
    return render(request, 'suppliers/register.html', {'form': form})


def registration_complete(request):
    supplier_name = request.session.pop('registered_supplier_name', None)
    if not supplier_name:
        return redirect('suppliers:register')
    return render(request, 'suppliers/registration_complete.html', {'supplier_name': supplier_name})


def statement(request, token):
    supplier = get_object_or_404(Supplier, statement_token=token, active=True)
    products = supplier.products.select_related('category').order_by('-received_at', 'name')
    sold_products = products.filter(sold=True).select_related('sale_items__sale')
    available_products = products.filter(sold=False)
    return render(request, 'suppliers/statement.html', {
        'supplier': supplier,
        'sold_products': sold_products,
        'available_products': available_products,
        'payments': supplier.payments.all(),
        'total_earned': supplier.total_earned,
        'total_paid': supplier.total_paid,
        'outstanding_balance': supplier.outstanding_balance,
    })
