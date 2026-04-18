from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q18 PROBLEM: A migration that adds a NOT NULL column without a default,
    or changes a field to NOT NULL when existing rows already have NULL values,
    will fail in production because the data violates the new schema constraint.

    This is a common "migration fails in production but works locally" issue
    because local dev DBs are empty or freshly migrated, while production has
    millions of rows with legacy data.
    """
    help = 'Q18 Problem: Migration fails because existing data violates schema constraint'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q18 PROBLEM: Migration fails due to data violating new constraint')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Create orders with NULL-equivalent fields (simulate legacy data)
        Order.objects.create(
            order_number='Q18-ORDER-1',
            customer_email='q18@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
            total=Decimal('0.00'),  # "empty" total — legacy data before total was required
        )
        self.stdout.write('Created legacy order with total=0.00 (simulates missing data)')

        # PROBLEM: simulate adding a NOT NULL constraint to an existing column
        # that has rows with zero/empty values (equivalent to NULL in business logic)
        self.stdout.write('\nSimulating migration: ALTER TABLE to add NOT NULL constraint...')
        try:
            with connection.cursor() as cursor:
                # SQLite does not support ALTER COLUMN, but this shows the concept.
                # In Postgres this would be:
                # ALTER TABLE orders_order ALTER COLUMN total SET NOT NULL;
                # ... which fails if any row has NULL or violates a CHECK constraint.
                raise Exception(
                    "django.db.utils.IntegrityError: column 'total' contains null values\n"
                    "  HINT: Provide a default or backfill data before adding NOT NULL."
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nMigration would fail with:\n  {e}'))

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Migration runs fine locally (empty DB) but crashes in production')
        self.stdout.write('  - Partial migration leaves schema in inconsistent state')
        self.stdout.write('  - Can cause downtime if migration blocks table during ALTER')
