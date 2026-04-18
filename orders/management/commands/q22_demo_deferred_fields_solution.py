from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q22 SOLUTION: Always include every field you will access in only(),
    OR avoid only()/defer() for code paths that access many fields.
    For projections, use values() or values_list() which return dicts/tuples
    and never trigger lazy field loading.
    """
    help = 'Q22 Solution: Include all needed fields in only() or use values()/values_list()'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q22 SOLUTION: Avoid deferred field N+1 queries')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q22-SOL-ORDER-{i}',
                customer_email=f'q22sol_{i}@example.com',
                amount=Decimal(f'{i * 10}.00'),
                price=Decimal(f'{i * 10}.00'),
            )
        self.stdout.write('Created 3 orders\n')

        settings.DEBUG = True

        # SOLUTION 1: Include ALL fields you will access in only()
        self.stdout.write('--- Solution 1: Include all needed fields in only() ---')
        reset_queries()
        orders = list(Order.objects.only('order_number', 'customer_email'))
        emails = [o.customer_email for o in orders]
        self.stdout.write(self.style.SUCCESS(
            f'Queries: {len(connection.queries)} (no extra queries — field included in only())'
        ))
        self.stdout.write(f'  Emails: {emails}')

        # SOLUTION 2: Use values() — returns dicts, no deferred fields possible
        self.stdout.write('\n--- Solution 2: Use values() to avoid model instances entirely ---')
        reset_queries()
        data = list(Order.objects.values('order_number', 'customer_email'))
        self.stdout.write(self.style.SUCCESS(
            f'Queries with values(): {len(connection.queries)} (1 query, dict result)'
        ))
        self.stdout.write(f'  First row: {data[0]}')

        # SOLUTION 3: Use values_list() for simple projections
        self.stdout.write('\n--- Solution 3: Use values_list() for tuple projections ---')
        reset_queries()
        pairs = list(Order.objects.values_list('order_number', 'amount'))
        self.stdout.write(self.style.SUCCESS(
            f'Queries with values_list(): {len(connection.queries)} (1 query)'
        ))

        settings.DEBUG = False
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always list every field you will access in only()')
        self.stdout.write('  - Use values()/values_list() for read-only projections')
        self.stdout.write('  - Avoid defer() unless you are certain you will never access those fields')
        self.stdout.write('  - Use django-debug-toolbar to catch deferred field hits in development')
