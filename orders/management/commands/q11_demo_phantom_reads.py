from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q11 PROBLEM: Phantom reads occur when a transaction reads a set of rows,
    then another transaction inserts new rows that match the same query,
    and the first transaction re-reads to find "phantom" rows it did not see
    before. The default SQLite/PostgreSQL READ COMMITTED isolation level
    allows this.

    NOTE: SQLite serialises writes so a true concurrent demo requires multiple
    threads or processes. This demo simulates the scenario sequentially to
    illustrate the concept clearly.
    """
    help = 'Q11 Problem: Phantom reads under READ COMMITTED isolation'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q11 PROBLEM: Phantom reads (READ COMMITTED isolation)')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        Order.objects.create(
            order_number='Q11-ORDER-1',
            customer_email='q11@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Transaction A: Read 1 — counting orders...')
        with transaction.atomic():
            count_first = Order.objects.count()
            self.stdout.write(f'  TX-A sees {count_first} order(s)')

            # Simulate TX-B inserting a new row between TX-A's two reads
            self.stdout.write('\nTransaction B (concurrent): Inserting a new order...')
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO orders_order "
                    "(order_number, customer_email, amount, price, total, created_at) "
                    "VALUES ('Q11-PHANTOM', 'phantom@example.com', 50, 50, 0, datetime('now'))"
                )
            self.stdout.write('  TX-B committed Q11-PHANTOM')

            # TX-A re-reads — under READ COMMITTED it sees the phantom row
            self.stdout.write('\nTransaction A: Read 2 — re-counting orders...')
            count_second = Order.objects.count()
            self.stdout.write(f'  TX-A now sees {count_second} order(s)')

        if count_second != count_first:
            self.stdout.write(self.style.ERROR(
                f'PHANTOM READ detected: count changed from {count_first} to {count_second} within TX-A'
            ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Business logic relying on consistent read counts within a TX will produce wrong results')
        self.stdout.write('  - Hard to reproduce in testing; only appears under concurrent load')
