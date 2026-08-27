from datetime import date
from decimal import Decimal

from django.db import migrations, models


def populate_effective_rates(apps, schema_editor):
    Supplier = apps.get_model('suppliers', 'Supplier')
    deadline = date(2026, 9, 11)
    for supplier in Supplier.objects.all():
        if supplier.consignment_rate is not None:
            supplier.use_automatic_rate = False
        else:
            supplier.consignment_rate = Decimal('0.50') if supplier.joined_at <= deadline else Decimal('0.30')
        supplier.save(update_fields=['consignment_rate', 'use_automatic_rate'])


class Migration(migrations.Migration):
    dependencies = [('suppliers', '0002_supplier_consignment_rate_override')]

    operations = [
        migrations.RenameField(
            model_name='supplier',
            old_name='consignment_rate_override',
            new_name='consignment_rate',
        ),
        migrations.AddField(
            model_name='supplier',
            name='use_automatic_rate',
            field=models.BooleanField(
                default=True,
                help_text='When enabled, sale and campaign dates determine the rate. Disable to force the selected rate.',
                verbose_name='Automatic calculation',
            ),
        ),
        migrations.RunPython(populate_effective_rates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='supplier',
            name='consignment_rate',
            field=models.DecimalField(
                choices=[(Decimal('0.50'), 'Force 50%'), (Decimal('0.30'), 'Force 30%')],
                decimal_places=2,
                default=Decimal('0.30'),
                help_text='Filled automatically from the campaign dates. Administrators may change it.',
                max_digits=4,
                verbose_name='Consignment rate',
            ),
        ),
    ]
