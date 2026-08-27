import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def populate_statement_tokens(apps, schema_editor):
    Supplier = apps.get_model('suppliers', 'Supplier')
    for supplier in Supplier.objects.all():
        supplier.statement_token = uuid.uuid4()
        supplier.save(update_fields=['statement_token'])


class Migration(migrations.Migration):
    dependencies = [('suppliers', '0003_supplier_effective_consignment_rate')]

    operations = [
        migrations.AddField(
            model_name='supplier', name='statement_token',
            field=models.UUIDField(null=True),
        ),
        migrations.RunPython(populate_statement_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='supplier', name='statement_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.CreateModel(
            name='SupplierPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, help_text='Total balance transferred to this supplier.', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('paid_at', models.DateField(default=django.utils.timezone.localdate, verbose_name='Payment date')),
                ('receipt', models.FileField(help_text='Receipt for the total supplier balance payment. Accepted: PDF or image.', upload_to='supplier-balance-receipts/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg', 'webp'])])),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='suppliers.supplier')),
            ],
            options={
                'verbose_name': 'Supplier balance payment',
                'verbose_name_plural': 'Supplier balance payments',
                'ordering': ['-paid_at', '-created_at'],
            },
        ),
    ]
