from django.contrib import admin

from .models import Customer, Sale, SaleItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'cpf', 'created_at')
    search_fields = ('name', 'email', 'cpf')
    date_hierarchy = 'created_at'


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ('product', 'price', 'supplier_rate', 'supplier_amount', 'language_center_amount', 'owner_amount')
    readonly_fields = ('product', 'price', 'supplier_amount', 'language_center_amount', 'owner_amount')
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if 'supplier_rate' in formset.form.base_fields:
            formset.form.base_fields['supplier_rate'].help_text = (
                'Calculated automatically at checkout. Administrators may change it here for this sale only.'
            )
        return formset


@admin.action(description='Mark selected sales as paid and send receipts')
def mark_sales_paid(modeladmin, request, queryset):
    for sale in queryset.filter(status='pending'):
        sale.mark_paid()


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_at', 'status', 'total', 'payment_reference')
    list_filter = ('status', 'created_at', 'items__product__supplier')
    search_fields = ('id', 'customer__name', 'customer__email', 'customer__cpf', 'payment_reference', 'items__product__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'total')
    inlines = (SaleItemInline,)
    actions = (mark_sales_paid,)


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'supplier', 'price', 'supplier_rate', 'supplier_amount', 'customer', 'sale_date')
    list_filter = ('supplier_rate', 'product__supplier', 'sale__status', 'sale__created_at')
    search_fields = ('product__name', 'product__code', 'product__supplier__name', 'sale__customer__name', 'sale__customer__cpf')
    list_select_related = ('sale', 'sale__customer', 'product', 'product__supplier')

    @admin.display(ordering='product__supplier__name')
    def supplier(self, obj):
        return obj.product.supplier

    @admin.display(ordering='sale__customer__name')
    def customer(self, obj):
        return obj.sale.customer

    @admin.display(ordering='sale__created_at')
    def sale_date(self, obj):
        return obj.sale.created_at
