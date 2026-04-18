from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q5 PROBLEM: select_related() only works for ForeignKey / OneToOne relationships.
    Using it on a ManyToManyField does NOT eliminate N+1 queries because
    select_related cannot JOIN across M2M through-tables.
    """
    help = 'Q5 Problem: select_related() still causes N+1 on ForeignKey access'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q5 PROBLEM: select_related() still N+1 on ForeignKey')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Create 5 orders linked to the same tax via FK
        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q5-ORDER-{i}',
                customer_email=f'q5_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
                tax=tax,
            )

        settings.DEBUG = True
        reset_queries()

        # PROBLEM: without select_related, each order.tax access hits the DB
        self.stdout.write('Accessing order.tax.name for each order WITHOUT select_related:')
        orders = Order.objects.all()  # no select_related
        for order in orders:
            _ = order.tax.name if order.tax else None  # N+1: 1 query per order

        query_count = len(connection.queries)
        self.stdout.write(self.style.ERROR(
            f'  Total DB queries: {query_count}  (1 list query + 1 per order = N+1 problem)'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - With 1000 orders this becomes 1001 DB queries')
        self.stdout.write('  - Each extra query has network/IO overhead')
        self.stdout.write('  - Performance degrades linearly with data set size')
        settings.DEBUG = False
