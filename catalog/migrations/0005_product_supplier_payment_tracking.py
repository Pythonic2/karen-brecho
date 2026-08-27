import django.core.validators
from django.db import migrations, models


def reset_legacy_customer_payment_flags(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    # The old field was set when the customer paid. It did not prove that the
    # supplier had received a payout, so it must not be carried forward as one.
    Product.objects.update(supplier_paid=False)


class Migration(migrations.Migration):
    dependencies = [('catalog', '0004_category_image_product_image')]

    operations = [
        migrations.RenameField(model_name='product', old_name='paid', new_name='supplier_paid'),
        migrations.AlterField(
            model_name='product', name='supplier_paid',
            field=models.BooleanField(
                default=False,
                help_text='This means the supplier — not the customer — has received payment for this piece.',
                verbose_name='Supplier paid',
            ),
        ),
        migrations.AddField(
            model_name='product', name='supplier_paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Supplier paid at'),
        ),
        migrations.AddField(
            model_name='product', name='supplier_payment_notes',
            field=models.TextField(
                blank=True,
                help_text='Optional notes about the transfer, PIX reference or payment adjustment.',
                verbose_name='Supplier payment notes',
            ),
        ),
        migrations.AddField(
            model_name='product', name='supplier_payment_receipt',
            field=models.FileField(
                blank=True,
                help_text='Required when marking the supplier as paid. Accepted: PDF, PNG, JPG, JPEG or WEBP.',
                upload_to='supplier-payment-receipts/%Y/%m/',
                validators=[django.core.validators.FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg', 'webp'])],
            ),
        ),
        migrations.RunPython(reset_legacy_customer_payment_flags, migrations.RunPython.noop),
    ]
