from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q22 PROBLEM: Django's only() and defer() create model instances with
    "deferred fields". Accessing a deferred field triggers an additional
    SELECT for each instance, creating N+1 queries silently.

    This is especially insidious because the code looks correct — the field
    access is just a Python attribute lookup — but it fires a DB query.
    """
    help = 'Q22 Problem: Deferred fields via only()/defer() cause silent N+1 queries'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q22 PROBLEM: Deferred fields cause hidden N+1 queries')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q22-ORDER-{i}',
                customer_email=f'q22_{i}@example.com',
                amount=Decimal(f'{i * 10}.00'),
                price=Decimal(f'{i * 10}.00'),
            )
        self.stdout.write('Created 3 orders\n')

        settings.DEBUG = True
        reset_queries()

        # PROBLEM: only('order_number') defers 'amount' and 'customer_email'
        orders = list(Order.objects.only('order_number'))
        self.stdout.write(f'Queries after only("order_number"): {len(connection.queries)}')

        reset_queries()
        # Accessing deferred field fires a NEW query per instance!
        emails = []
        for order in orders:
            emails.append(order.customer_email)   # HIDDEN DB HIT per order

        deferred_queries = len(connection.queries)
        self.stdout.write(self.style.ERROR(
            f'PROBLEM: Accessing deferred field fired {deferred_queries} extra queries '
            f'(1 per order instance)'
        ))
        self.stdout.write(f'  Emails retrieved: {emails}')

        settings.DEBUG = False
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - No exception raised — looks like normal attribute access')
        self.stdout.write('  - Each deferred field access = 1 extra SELECT')
        self.stdout.write('  - With 1000 rows, accessing 3 deferred fields = 3000 extra queries')
