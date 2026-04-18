from decimal import Decimal

from django.core.management.base import BaseCommand
from django import db

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q19 PROBLEM: Django opens one DB connection per process/thread and does
    NOT use a connection pool by default. Under high concurrency this means:
      - Many short-lived connections hit the DB server's max_connections limit
      - Each Django worker opens its own connection (no sharing)
      - Connection setup/teardown overhead on every request

    This demo shows how quickly connections pile up without pooling.
    """
    help = 'Q19 Problem: No connection pooling — each process opens its own DB connection'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q19 PROBLEM: Django has no built-in connection pooling')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        self.stdout.write('Django DB connection behaviour:')
        conn = db.connection
        self.stdout.write(f'  Current connection: {conn.alias} (vendor: {conn.vendor})')
        self.stdout.write(f'  Connection is open: {conn.connection is not None}')

        # Show that Django creates/closes connections per request
        Order.objects.create(
            order_number='Q19-ORDER-1',
            customer_email='q19@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'  After query — connection open: {conn.connection is not None}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: In production with 100 gunicorn workers, each worker opens '
            'its own persistent connection. With 100 workers × 4 threads = 400 connections '
            'to the DB — most DBs default max_connections=100.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - DB server runs out of connections under load')
        self.stdout.write('  - "FATAL: remaining connection slots are reserved" errors')
        self.stdout.write('  - No reuse of idle connections across requests')
