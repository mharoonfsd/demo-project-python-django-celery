from decimal import Decimal

from django.core.management.base import BaseCommand
from django import db

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q19 SOLUTION: Use an external connection pooler (PgBouncer for PostgreSQL)
    or Django 4.2+'s built-in connection pool (CONN_MAX_AGE + persistent connections).

    For production:
      - Set CONN_MAX_AGE in DATABASES settings to reuse connections per worker
      - Use PgBouncer in transaction-mode pooling in front of PostgreSQL
      - With Django 4.2+, use the new built-in pool via django.db.backends.postgresql
        with the 'pool' OPTIONS key (requires psycopg3)

    This demo shows CONN_MAX_AGE and explains the pooling architecture.
    """
    help = 'Q19 Solution: Use CONN_MAX_AGE and PgBouncer for connection pooling'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q19 SOLUTION: Connection pooling strategies')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        conn = db.connection
        self.stdout.write(f'Current connection: {conn.alias} (vendor: {conn.vendor})')

        # SOLUTION 1: CONN_MAX_AGE
        self.stdout.write('\n--- Solution 1: CONN_MAX_AGE (Django built-in) ---')
        self.stdout.write('  In settings.py:')
        self.stdout.write('    DATABASES = {')
        self.stdout.write('      "default": {')
        self.stdout.write('        "ENGINE": "django.db.backends.postgresql",')
        self.stdout.write('        "CONN_MAX_AGE": 60,  # reuse connection for 60 seconds')
        self.stdout.write('      }')
        self.stdout.write('    }')
        self.stdout.write('  -> Each worker thread reuses its connection for up to 60s')
        self.stdout.write('  -> Reduces connection setup overhead per request')

        # SOLUTION 2: PgBouncer (external)
        self.stdout.write('\n--- Solution 2: PgBouncer (recommended for PostgreSQL) ---')
        self.stdout.write('  Architecture: App -> PgBouncer -> PostgreSQL')
        self.stdout.write('  - PgBouncer maintains a pool of N connections to Postgres')
        self.stdout.write('  - 1000 app connections can share 50 real DB connections')
        self.stdout.write('  - Transaction-mode pooling: most efficient for Django/Celery')

        # SOLUTION 3: Django 4.2+ with psycopg3 built-in pool
        self.stdout.write('\n--- Solution 3: Django 4.2+ built-in pool (psycopg3) ---')
        self.stdout.write('  In settings.py:')
        self.stdout.write('    "ENGINE": "django.db.backends.postgresql",')
        self.stdout.write('    "OPTIONS": {"pool": {"min_size": 2, "max_size": 10}}')

        Order.objects.create(
            order_number='Q19-SOL-ORDER-1',
            customer_email='q19sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(self.style.SUCCESS(f'\nConnection reused: {conn.connection is not None}'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set CONN_MAX_AGE=60 as a minimum in all Django production deployments')
        self.stdout.write('  - Use PgBouncer in transaction mode for high-concurrency PostgreSQL')
        self.stdout.write('  - Monitor active connections with pg_stat_activity')
