import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from suppliers.models import Supplier


def generate_product_code():
    return str(uuid.uuid4().int)[-4:]


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=40, default='✦')
    image = models.ImageField(upload_to='category-icons/', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    code = models.CharField(max_length=100, unique=True, default=generate_product_code)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=255)
    received_at = models.DateField()
    listed_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    sold = models.BooleanField(default=False)
    sold_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='products/', blank=True,
        help_text='Optional product image. The category icon is used when left blank.',
    )

    class Meta:
        ordering = ['-received_at', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f'{self.name} · {self.code}'

    @property
    def is_available(self):
        return not self.sold

    @property
    def display_image(self):
        return self.image or self.category.image

    def supplier_share_rate(self, sale_date=None):
        from datetime import date
        # A manual supplier rate is managed only through Django Admin and is
        # never exposed in the supplier-facing form.
        if not self.supplier.use_automatic_rate:
            return self.supplier.consignment_rate
        sale_date = sale_date or date.today()
        period_start = date.fromisoformat(settings.CONSIGNMENT_PERIOD_START)
        deadline = date.fromisoformat(settings.CONSIGNMENT_HIGH_RATE_DEADLINE)
        high_rate = Decimal(settings.CONSIGNMENT_HIGH_RATE)
        standard_rate = Decimal(settings.CONSIGNMENT_STANDARD_RATE)
        # Automatic opening rule:
        # - supplier joined no later than the September 11 deadline;
        # - piece was received during the opening period, no later than the 11th;
        # - piece was sold during the opening period, no later than the 11th.
        # A new supplier, a new piece, or a sale after the deadline earns 30%.
        if (
            self.supplier.joined_at <= deadline
            and period_start <= self.received_at <= deadline
            and period_start <= sale_date <= deadline
        ):
            rate = high_rate
        else:
            rate = standard_rate
        # Keep the Supplier field meaningful in Admin while SaleItem still
        # freezes the historical rate used by each individual sale.
        if self.supplier.consignment_rate != rate:
            type(self.supplier).objects.filter(pk=self.supplier_id, use_automatic_rate=True).update(
                consignment_rate=rate
            )
            self.supplier.consignment_rate = rate
        return rate
