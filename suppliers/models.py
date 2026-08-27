from datetime import date
from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.core.mail import send_mail
from django.urls import reverse

class Supplier(models.Model):
    RATE_OVERRIDE_CHOICES = (
        (Decimal('0.50'), 'Force 50%'),
        (Decimal('0.30'), 'Force 30%'),
    )

    name = models.CharField(max_length=150)
    email = models.EmailField()
    cpf = models.CharField(max_length=14, unique=True)
    pix_key = models.CharField(max_length=255)
    consignment_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        choices=RATE_OVERRIDE_CHOICES,
        default=Decimal('0.30'),
        help_text='Filled automatically from the campaign dates. Administrators may change it.',
        verbose_name='Consignment rate',
    )
    use_automatic_rate = models.BooleanField(
        default=True,
        help_text='When enabled, sale and campaign dates determine the rate. Disable to force the selected rate.',
        verbose_name='Automatic calculation',
    )
    joined_at = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    statement_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding and self.use_automatic_rate:
            deadline = date.fromisoformat(settings.CONSIGNMENT_HIGH_RATE_DEADLINE)
            registration_date = self.joined_at or timezone.localdate()
            self.consignment_rate = (
                Decimal(settings.CONSIGNMENT_HIGH_RATE)
                if registration_date <= deadline
                else Decimal(settings.CONSIGNMENT_STANDARD_RATE)
            )
        super().save(*args, **kwargs)

    @property
    def consignment_rate_percent(self):
        return self.consignment_rate * Decimal('100')

    @property
    def consignment_rate_mode(self):
        mode = 'Automatic' if self.use_automatic_rate else 'Manual'
        return f'{mode} {self.consignment_rate_percent:.0f}%'

    @property
    def total_earned(self):
        from transactions.models import SaleItem
        return sum(
            (item.supplier_amount for item in SaleItem.objects.filter(
                product__supplier=self, sale__status='paid'
            )),
            Decimal('0'),
        )

    @property
    def total_paid(self):
        return sum((payment.amount for payment in self.payments.all()), Decimal('0'))

    @property
    def outstanding_balance(self):
        return self.total_earned - self.total_paid

    def statement_url(self):
        return f"{settings.SITE_BASE_URL.rstrip('/')}{reverse('suppliers:statement', args=[self.statement_token])}"

    def send_statement_email(self):
        url = self.statement_url()
        subject = "Your private Telles' Thrift Shop supplier statement"
        body = '\n'.join([
            f'Hello {self.name},',
            '',
            "Your supplier registration at Telles' Thrift Shop is complete.",
            '',
            'Use your private statement link to follow:',
            '- pieces available in the shop',
            '- pieces already sold',
            '- your share from each sale',
            '- total already paid',
            '- outstanding balance',
            '- payment receipts',
            '',
            url,
            '',
            'This link is private. Please do not share it with other people.',
            '',
            "Telles' Thrift Shop",
        ])
        return send_mail(subject, body, None, [self.email])


class SupplierPayment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Total balance transferred to this supplier.',
    )
    paid_at = models.DateField(default=timezone.localdate, verbose_name='Payment date')
    receipt = models.FileField(
        upload_to='supplier-balance-receipts/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg', 'webp'])],
        help_text='Receipt for the total supplier balance payment. Accepted: PDF or image.',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at', '-created_at']
        verbose_name = 'Supplier balance payment'
        verbose_name_plural = 'Supplier balance payments'

    def __str__(self):
        return f'{self.supplier} · R$ {self.amount:.2f} · {self.paid_at}'

    def clean(self):
        super().clean()
        if not self.receipt:
            raise ValidationError({'receipt': 'Upload the receipt for this balance payment.'})
        previous = sum(
            (payment.amount for payment in self.supplier.payments.exclude(pk=self.pk)),
            Decimal('0'),
        ) if self.supplier_id else Decimal('0')
        available = self.supplier.total_earned - previous if self.supplier_id else Decimal('0')
        if self.amount and self.amount > available:
            raise ValidationError({'amount': f'This payment exceeds the current outstanding balance of R$ {available:.2f}.'})
