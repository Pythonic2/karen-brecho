from django.test import TestCase
from django.urls import reverse
from django.core import mail

from .models import Supplier


class SupplierRegistrationTests(TestCase):
    def test_registration_has_no_rate_field_and_creates_supplier(self):
        response = self.client.get(reverse('suppliers:register'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="supplier_rate')
        self.assertNotContains(response, 'name="consignment_rate')

        response = self.client.post(reverse('suppliers:register'), {
            'name': 'Maria Supplier',
            'email': 'maria@example.com',
            'cpf': '12345678901',
            'pix_key': 'maria@example.com',
            'accept_terms': 'on',
        })
        self.assertRedirects(response, reverse('suppliers:registration_complete'), fetch_redirect_response=False)
        supplier = Supplier.objects.get()
        self.assertEqual(supplier.cpf, '123.456.789-01')
        self.assertTrue(supplier.active)
        self.assertEqual(supplier.consignment_rate, supplier.RATE_OVERRIDE_CHOICES[0][0])
        self.assertTrue(supplier.use_automatic_rate)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['maria@example.com'])
        self.assertIn(str(supplier.statement_token), mail.outbox[0].body)
        self.assertIn('This link is private', mail.outbox[0].body)
        statement = self.client.get(reverse('suppliers:statement', args=[supplier.statement_token]))
        self.assertContains(statement, 'Still to receive')

    def test_terms_and_unique_cpf_are_required(self):
        data = {'name': 'Maria', 'email': 'maria@example.com', 'cpf': '12345678901', 'pix_key': 'key'}
        response = self.client.post(reverse('suppliers:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Supplier.objects.exists())
        Supplier.objects.create(name='Existing', email='one@example.com', cpf='123.456.789-01', pix_key='one')
        data['accept_terms'] = 'on'
        response = self.client.post(reverse('suppliers:register'), data)
        self.assertContains(response, 'Supplier with this Cpf already exists.')
