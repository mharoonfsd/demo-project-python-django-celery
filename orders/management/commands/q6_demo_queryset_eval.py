from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q6 PROBLEM: A Django QuerySet is lazy — it is evaluated every time you
    iterate or call len() on it. If you store a QuerySet in a variable and
    access it twice, it hits the database twice.
    """
    help = 'Q6 Problem: QuerySet evaluated twice causes duplicate DB queries'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q6 PROBLEM: QuerySet evaluated twice')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q6-ORDER-{i}',
                customer_email=f'q6_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        settings.DEBUG = True
        reset_queries()

        # PROBLEM: qs is a lazy QuerySet — evaluated on each use
        qs = Order.objects.all()

        self.stdout.write('First access (iterates queryset):')
        count1 = len(qs)  # DB hit #1
        self.stdout.write(f'  count={count1}')

        self.stdout.write('Second access (iterates queryset again):')
        count2 = len(qs)  # DB hit #2 — same data fetched again!
        self.stdout.write(f'  count={count2}')

        query_count = len(connection.queries)
        self.stdout.write(self.style.ERROR(
            f'\nTotal DB queries: {query_count}  (expected 1, got {query_count} — QuerySet hit DB twice)'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Invisible extra DB round-trips under load')
        self.stdout.write('  - Inconsistent results if data changes between evaluations')
        settings.DEBUG = False
