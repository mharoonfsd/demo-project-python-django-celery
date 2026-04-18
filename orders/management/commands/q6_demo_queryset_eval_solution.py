from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q6 SOLUTION: Force evaluation of the QuerySet once by wrapping it in
    list(). The result is cached in memory; subsequent iterations do not
    hit the database again.
    """
    help = 'Q6 Solution: Cache queryset as list() to avoid double evaluation'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q6 SOLUTION: Force evaluate with list()')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q6-SOL-ORDER-{i}',
                customer_email=f'q6sol_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        settings.DEBUG = True
        reset_queries()

        # SOLUTION: evaluate the QuerySet once into a list
        orders = list(Order.objects.all())  # single DB hit, result cached in memory

        self.stdout.write('First access:')
        count1 = len(orders)  # reads from in-memory list — no DB
        self.stdout.write(f'  count={count1}')

        self.stdout.write('Second access:')
        count2 = len(orders)  # reads from in-memory list — no DB
        self.stdout.write(f'  count={count2}')

        query_count = len(connection.queries)
        self.stdout.write(self.style.SUCCESS(
            f'\nTotal DB queries: {query_count}  (exactly 1 — result cached in list)'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Wrap in list() to force evaluation and cache the result')
        self.stdout.write('  - Useful when you need to iterate or measure a queryset more than once')
        self.stdout.write('  - Be mindful of memory usage for very large querysets')
        settings.DEBUG = False
