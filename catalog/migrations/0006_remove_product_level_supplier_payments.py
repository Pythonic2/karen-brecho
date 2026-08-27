from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('catalog', '0005_product_supplier_payment_tracking')]

    operations = [
        migrations.RemoveField(model_name='product', name='supplier_paid'),
        migrations.RemoveField(model_name='product', name='supplier_paid_at'),
        migrations.RemoveField(model_name='product', name='supplier_payment_notes'),
        migrations.RemoveField(model_name='product', name='supplier_payment_receipt'),
    ]
