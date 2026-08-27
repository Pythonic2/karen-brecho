from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from catalog.models import Product

class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    cpf = models.CharField(max_length=14)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return self.name

class Sale(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')]
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'

    def __str__(self):
        return f'Sale #{self.pk} · {self.customer}'

    @transaction.atomic
    def mark_paid(self):
        if self.status == 'paid':
            return
        self.status = 'paid'
        self.save(update_fields=['status'])
        for item in self.items.select_related('product'):
            item.product.sold = True
            item.product.sold_price = item.price
            item.product.save(update_fields=['sold', 'sold_price'])
        send_mail(f'Telles Thrift Shop receipt #{self.pk}', self.receipt_text(), None, [self.customer.email])

    def receipt_text(self):
        lines = [f'Hello {self.customer.name},', '', f'Thank you for shopping at Telles Thrift Shop.', f'Sale #{self.pk}', '']
        for item in self.items.select_related('product'):
            lines.append(f'- {item.product.name}: R$ {item.price:.2f}')
        lines += ['', f'Total: R$ {self.total:.2f}', 'Payment: PIX (development simulation)']
        return '\n'.join(lines)

class SaleItem(models.Model):
    RATE_CHOICES = (
        (Decimal('0.50'), '50%'),
        (Decimal('0.30'), '30%'),
    )
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.OneToOneField(Product, on_delete=models.PROTECT, related_name='sale_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        choices=RATE_CHOICES,
        help_text='Initially calculated from the product rule; it can be corrected manually.',
    )

    class Meta:
        verbose_name = 'Sale item'
        verbose_name_plural = 'Sale items'

    @property
    def supplier_rate_percent(self):
        return (self.supplier_rate or Decimal('0')) * Decimal('100')

    @property
    def supplier_amount(self):
        if self.price is None or self.supplier_rate is None:
            return Decimal('0.00')
        return (self.price * self.supplier_rate).quantize(Decimal('0.01'))

    @property
    def shop_amount(self):
        return (self.price or Decimal('0')) - self.supplier_amount

    @property
    def language_center_amount(self):
        return (self.shop_amount * Decimal(settings.LANGUAGE_CENTER_RATE)).quantize(Decimal('0.01'))

    @property
    def owner_amount(self):
        return self.shop_amount - self.language_center_amount
