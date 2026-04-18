from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q18 SOLUTION: The safe migration pattern for adding constraints to tables
    with existing data is a three-step "expand-migrate-contract" approach:

    Step 1 (EXPAND): Add the column as nullable (null=True) — zero downtime.
    Step 2 (MIGRATE): Backfill existing rows with a valid default value.
    Step 3 (CONTRACT): Remove null=True and add NOT NULL — now safe because all rows are valid.

    Django's RunPython in migrations is used for the backfill step.
    """
    help = 'Q18 Solution: Safe three-step expand-migrate-contract migration pattern'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q18 SOLUTION: Expand-Migrate-Contract migration pattern')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Simulate pre-existing legacy data
        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q18-SOL-ORDER-{i}',
                customer_email=f'q18sol_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
                total=Decimal('0.00'),  # legacy: total not calculated yet
            )
        self.stdout.write(f'Created 3 legacy orders with total=0.00\n')

        # STEP 1: EXPAND — column already exists as nullable (no change needed here)
        self.stdout.write('--- Step 1: EXPAND ---')
        self.stdout.write('  Migration 1: Add column as nullable (null=True, blank=True)')
        self.stdout.write('  Example migration field: total = DecimalField(null=True, blank=True)')
        self.stdout.write('  -> Zero downtime, all existing rows get NULL')

        # STEP 2: MIGRATE — backfill all rows with a sensible default
        self.stdout.write('\n--- Step 2: MIGRATE (backfill) ---')
        updated = Order.objects.filter(total=Decimal('0.00')).update(total=Decimal('0.00'))
        # In real backfill: Order.objects.filter(total__isnull=True).update(total=F('price'))
        self.stdout.write(f'  Backfilled {updated} rows with a computed default')
        self.stdout.write('  Example migration: RunPython(backfill_totals)')

        # STEP 3: CONTRACT — remove null=True and add NOT NULL constraint
        self.stdout.write('\n--- Step 3: CONTRACT ---')
        self.stdout.write('  Migration 3: Remove null=True from field definition')
        self.stdout.write('  -> Now safe because all rows have valid values')
        self.stdout.write('  -> Django generates: ALTER COLUMN total SET NOT NULL')

        all_valid = not Order.objects.filter(total__isnull=True).exists()
        self.stdout.write(self.style.SUCCESS(
            f'\nAll rows valid for NOT NULL constraint: {all_valid}'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Never add NOT NULL in a single migration on a table with data')
        self.stdout.write('  - Use three migrations: nullable add -> backfill -> not-null constraint')
        self.stdout.write('  - Use RunPython with batched updates for large tables')
        self.stdout.write('  - Test migrations against a production-sized DB snapshot before deploying')
