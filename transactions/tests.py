from datetime import date
from decimal import Decimal

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from suppliers.models import Supplier
from suppliers.models import SupplierPayment
from .models import Sale


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            name='Ana Supplier', email='ana@example.com', cpf='111.222.333-44', pix_key='ana@example.com'
        )
        self.category = Category.objects.create(name='Dress', slug='dress', icon='👗')
        self.product = Product.objects.create(
            code='1234', supplier=self.supplier, category=self.category, name='Red dress',
            received_at=date(2026, 9, 7), listed_price=Decimal('100.00'),
        )

    def test_campaign_rate_and_standard_rate(self):
        self.assertEqual(self.product.supplier_share_rate(date(2026, 9, 11)), Decimal('0.50'))
        self.assertEqual(self.product.supplier_share_rate(date(2026, 9, 12)), Decimal('0.30'))
        self.product.received_at = date(2026, 9, 12)
        self.assertEqual(self.product.supplier_share_rate(date(2026, 9, 11)), Decimal('0.30'))
        self.supplier.consignment_rate = Decimal('0.50')
        self.supplier.use_automatic_rate = False
        self.assertEqual(self.product.supplier_share_rate(date(2026, 9, 18)), Decimal('0.50'))

    def test_supplier_joining_after_deadline_gets_standard_rate(self):
        Supplier.objects.filter(pk=self.supplier.pk).update(joined_at=date(2026, 9, 12))
        self.supplier.refresh_from_db()
        self.supplier.use_automatic_rate = True
        self.assertEqual(self.product.supplier_share_rate(date(2026, 9, 11)), Decimal('0.30'))

    def test_empty_admin_inline_calculations_do_not_fail(self):
        from .models import SaleItem
        empty_item = SaleItem()
        self.assertEqual(empty_item.supplier_amount, Decimal('0.00'))
        self.assertEqual(empty_item.language_center_amount, Decimal('0.00'))

    def test_complete_fake_pix_flow_records_parties_and_sends_receipt(self):
        self.client.post(reverse('transactions:add_to_cart', args=[self.product.id]))
        response = self.client.post(reverse('transactions:checkout'), {
            'name': 'John Customer', 'email': 'john@example.com', 'cpf': '555.666.777-88',
            'accept_terms': 'on',
        })
        self.assertRedirects(response, reverse('transactions:complete'))
        sale = Sale.objects.get()
        self.assertEqual(self.client.get(reverse('transactions:complete')).status_code, 200)
        self.assertEqual(sale.customer.name, 'John Customer')
        self.assertEqual(sale.items.get().product.supplier, self.supplier)
        response = self.client.post(reverse('transactions:simulate_payment'))
        self.assertRedirects(response, reverse('transactions:complete'))
        sale.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(sale.status, 'paid')
        self.assertTrue(self.product.sold)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Red dress', mail.outbox[0].body)

        user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'test-password')
        self.client.force_login(user)
        admin_change = self.client.get(reverse('admin:transactions_sale_change', args=[sale.id]))
        self.assertEqual(admin_change.status_code, 200)
        report = self.client.get(reverse('reports:sales_report'))
        self.assertContains(report, 'Ana Supplier')
        self.assertContains(report, '30%')
        self.assertContains(report, 'R$ 30.00')

        payment = SupplierPayment(
            supplier=self.supplier,
            amount=Decimal('20.00'),
            receipt=SimpleUploadedFile('balance.pdf', b'%PDF-1.4 demo', content_type='application/pdf'),
            notes='Partial balance transfer',
        )
        payment.full_clean()
        payment.save()
        statement = self.client.get(reverse('suppliers:statement', args=[self.supplier.statement_token]))
        self.assertContains(statement, 'R$ 30.00')
        self.assertContains(statement, 'R$ 20.00')
        self.assertContains(statement, 'R$ 10.00')

    def test_terms_are_required(self):
        self.client.post(reverse('transactions:add_to_cart', args=[self.product.id]))
        response = self.client.post(reverse('transactions:checkout'), {
            'name': 'John Customer', 'email': 'john@example.com', 'cpf': '555.666.777-88',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Sale.objects.exists())
