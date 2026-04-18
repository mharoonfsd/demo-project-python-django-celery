from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q5 SOLUTION: Use select_related() for ForeignKey/OneToOne relationships
    to JOIN in a single SQL query, eliminating N+1 hits.
    """
    help = 'Q5 Solution: Use select_related() to eliminate N+1 on ForeignKey'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q5 SOLUTION: select_related() eliminates N+1 for FK')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q5-SOL-ORDER-{i}',
                customer_email=f'q5sol_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
                tax=tax,
            )

        settings.DEBUG = True
        reset_queries()

        # SOLUTION: select_related JOINs Tax in a single query
        self.stdout.write('Accessing order.tax.name for each order WITH select_related:')
        orders = Order.objects.select_related('tax').all()
        for order in orders:
            _ = order.tax.name if order.tax else None  # no extra query — already JOINed

        query_count = len(connection.queries)
        self.stdout.write(self.style.SUCCESS(
            f'  Total DB queries: {query_count}  (single JOIN query — no N+1)'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - select_related() works for ForeignKey and OneToOne fields')
        self.stdout.write('  - It adds a SQL JOIN, fetching related objects in one query')
        self.stdout.write('  - For ManyToMany use prefetch_related() instead')
        settings.DEBUG = False
