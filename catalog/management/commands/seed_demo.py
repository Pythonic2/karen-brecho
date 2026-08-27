from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Category, Product
from suppliers.models import Supplier
from transactions.models import Customer, Sale, SaleItem


class Command(BaseCommand):
    help = 'Create idempotent demo categories, suppliers, products, and paid sales.'

    categories = (
        ('Dress', 'dress', '👗', 'category-icons/dress.png'),
        ('Skirt', 'skirt', '◒', 'category-icons/skirt.png'),
        ('Trousers', 'trousers', '👖', 'category-icons/trousers.png'),
        ('Shorts', 'shorts', '▱', 'category-icons/shorts.png'),
        ('Shirt', 'shirt', '👚', 'category-icons/shirt.png'),
        ('Jacket', 'jacket', '🧥', 'category-icons/jacket.png'),
    )

    suppliers = (
        ('Demo · Alice Vintage', 'alice.demo@example.com', '900.000.000-01', 'alice-demo-pix', Decimal('0.50'), True, date(2026, 9, 7)),
        ('Demo · Bruno Closet', 'bruno.demo@example.com', '900.000.000-02', 'bruno-demo-pix', Decimal('0.30'), True, date(2026, 9, 12)),
        ('Demo · Clara Collection', 'clara.demo@example.com', '900.000.000-03', 'clara-demo-pix', Decimal('0.50'), False, date(2026, 9, 14)),
        ('Demo · Daniel Wardrobe', 'daniel.demo@example.com', '900.000.000-04', 'daniel-demo-pix', Decimal('0.30'), False, date(2026, 9, 8)),
    )

    product_names = {
        'dress': ('Floral Midi Dress', 'Classic Burgundy Dress', 'Soft Summer Dress'),
        'skirt': ('Pleated Rose Skirt', 'Vintage A-line Skirt', 'Everyday Midi Skirt'),
        'trousers': ('Wide-leg Trousers', 'Classic Tailored Trousers', 'Relaxed Cotton Trousers'),
        'shorts': ('High-waist Shorts', 'Tailored Summer Shorts', 'Casual Cuffed Shorts'),
        'shirt': ('Soft Button-up Shirt', 'Oversized Cotton Shirt', 'Classic Collared Shirt'),
        'jacket': ('Vintage Denim Jacket', 'Lightweight Jacket', 'Classic Cropped Jacket'),
    }

    def handle(self, *args, **options):
        categories = {}
        for name, slug, emoji, image in self.categories:
            category, _ = Category.objects.update_or_create(
                slug=slug, defaults={'name': name, 'icon': emoji, 'image': image}
            )
            categories[slug] = category

        suppliers = []
        for name, email, cpf, pix, rate, automatic, joined_at in self.suppliers:
            supplier, _ = Supplier.objects.update_or_create(
                cpf=cpf,
                defaults={
                    'name': name, 'email': email, 'pix_key': pix, 'active': True,
                    'consignment_rate': rate, 'use_automatic_rate': automatic,
                },
            )
            Supplier.objects.filter(pk=supplier.pk).update(joined_at=joined_at)
            supplier.refresh_from_db()
            suppliers.append(supplier)

        products = []
        price = Decimal('39.90')
        index = 0
        for slug, names in self.product_names.items():
            category = categories[slug]
            for name in names:
                supplier = suppliers[index % len(suppliers)]
                received_at = date(2026, 9, 8) if index % 2 == 0 else date(2026, 9, 13)
                product, _ = Product.objects.update_or_create(
                    supplier=supplier,
                    name=f'Demo · {name}',
                    defaults={
                        'category': category,
                        'received_at': received_at,
                        'listed_price': price + Decimal(index * 5),
                        'description': 'Demo piece in excellent pre-loved condition.',
                        'image': category.image.name,
                    },
                )
                products.append(product)
                index += 1

        customer, _ = Customer.objects.update_or_create(
            cpf='999.000.000-00',
            defaults={'name': 'Demo Customer', 'email': 'customer.demo@example.com'},
        )
        self.create_paid_sale(customer, products[:2], 'DEMO-PIX-50', date(2026, 9, 10), Decimal('0.50'))
        self.create_paid_sale(customer, products[2:5], 'DEMO-PIX-30', date(2026, 9, 14), Decimal('0.30'))
        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready: {len(categories)} categories, {len(suppliers)} suppliers, '
            f'{len(products)} products, and 2 paid sales.'
        ))

    def create_paid_sale(self, customer, products, reference, sale_date, rate):
        sale, created = Sale.objects.get_or_create(
            payment_reference=reference,
            defaults={'customer': customer, 'status': 'paid', 'total': Decimal('0')},
        )
        if not created:
            return sale
        total = Decimal('0')
        for product in products:
            if not hasattr(product, 'sale_items'):
                SaleItem.objects.create(sale=sale, product=product, price=product.listed_price, supplier_rate=rate)
                product.sold = True
                product.sold_price = product.listed_price
                product.save(update_fields=['sold', 'sold_price'])
                total += product.listed_price
        sale.total = total
        sale.save(update_fields=['total'])
        aware_date = timezone.make_aware(datetime.combine(sale_date, datetime.min.time().replace(hour=12)))
        Sale.objects.filter(pk=sale.pk).update(created_at=aware_date)
        return sale
