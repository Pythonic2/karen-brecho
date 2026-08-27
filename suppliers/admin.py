from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Supplier, SupplierPayment


class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 0
    fields = ('amount', 'paid_at', 'receipt', 'notes')


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'amount', 'paid_at', 'receipt', 'created_at')
    list_filter = ('paid_at', 'supplier')
    search_fields = ('supplier__name', 'supplier__cpf', 'notes')
    autocomplete_fields = ('supplier',)
    date_hierarchy = 'paid_at'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'cpf', 'consignment_rate_mode', 'total_earned_display', 'total_paid_display', 'outstanding_display', 'statement_link', 'active')
    list_filter = ('active', 'use_automatic_rate', 'consignment_rate', 'joined_at')
    search_fields = ('name', 'email', 'cpf', 'pix_key')
    date_hierarchy = 'joined_at'
    inlines = (SupplierPaymentInline,)
    readonly_fields = ('supplier_statement_url', 'balance_summary')
    fieldsets = (
        ('Supplier details', {'fields': ('name', 'email', 'cpf', 'pix_key', 'active', 'supplier_statement_url')}),
        ('Consignment — administrators only', {
            'fields': ('consignment_rate', 'use_automatic_rate'),
            'description': (
                'The rate is filled automatically. To make an exception, disable automatic '
                'calculation and select 50% or 30%.'
            ),
        }),
        ('Current balance', {'fields': ('balance_summary',)}),
    )

    @admin.display(description='Supplier statement URL')
    def supplier_statement_url(self, obj):
        if not obj.pk:
            return 'Available after saving the supplier.'
        url = obj.statement_url()
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description='Statement')
    def statement_link(self, obj):
        return format_html('<a href="{}" target="_blank">Open</a>', reverse('suppliers:statement', args=[obj.statement_token]))

    @admin.display(description='Balance summary')
    def balance_summary(self, obj):
        if not obj.pk:
            return 'Available after saving the supplier.'
        return f'Earned: R$ {obj.total_earned:.2f} · Paid: R$ {obj.total_paid:.2f} · Outstanding: R$ {obj.outstanding_balance:.2f}'

    @admin.display(description='Earned')
    def total_earned_display(self, obj):
        return f'R$ {obj.total_earned:.2f}'

    @admin.display(description='Paid')
    def total_paid_display(self, obj):
        return f'R$ {obj.total_paid:.2f}'

    @admin.display(description='Outstanding')
    def outstanding_display(self, obj):
        return f'R$ {obj.outstanding_balance:.2f}'
