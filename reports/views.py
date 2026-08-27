from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from suppliers.models import Supplier

from transactions.models import SaleItem


@login_required
def sales_report(request):
    items = SaleItem.objects.filter(sale__status='paid').select_related(
        'sale', 'sale__customer', 'product', 'product__supplier'
    )
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')
    supplier_id = request.GET.get('supplier', '')
    if start:
        items = items.filter(sale__created_at__date__gte=start)
    if end:
        items = items.filter(sale__created_at__date__lte=end)
    if supplier_id:
        items = items.filter(product__supplier_id=supplier_id)

    supplier_rows = []
    totals = {'sales': 0, 'supplier': 0, 'supplier_paid': 0, 'supplier_outstanding': 0, 'center': 0, 'owner': 0}
    grouped = {}
    for item in items:
        row = grouped.setdefault(item.product.supplier_id, {
            'supplier': item.product.supplier, 'items': [], 'sales': Decimal('0'),
            'supplier_amount': Decimal('0'), 'center_amount': Decimal('0'), 'owner_amount': Decimal('0'),
            'supplier_paid_amount': Decimal('0'), 'supplier_outstanding_amount': Decimal('0'),
        })
        row['items'].append(item)
        row['sales'] += item.price
        row['supplier_amount'] += item.supplier_amount
        row['center_amount'] += item.language_center_amount
        row['owner_amount'] += item.owner_amount
        totals['sales'] += item.price
        totals['supplier'] += item.supplier_amount
        totals['center'] += item.language_center_amount
        totals['owner'] += item.owner_amount
    for row in grouped.values():
        row['supplier_paid_amount'] = row['supplier'].total_paid
        row['supplier_outstanding_amount'] = row['supplier'].outstanding_balance
        row['payments'] = row['supplier'].payments.all()
        totals['supplier_paid'] += row['supplier_paid_amount']
        totals['supplier_outstanding'] += row['supplier_outstanding_amount']
    supplier_rows = sorted(grouped.values(), key=lambda row: row['supplier'].name.lower())
    return render(request, 'reports/sales_report.html', {
        'supplier_rows': supplier_rows, 'totals': totals, 'suppliers': Supplier.objects.filter(active=True),
        'selected_supplier': supplier_id, 'start': start, 'end': end,
    })
