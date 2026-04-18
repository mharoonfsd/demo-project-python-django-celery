from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q91 SOLUTION: Make pipeline idempotent. Use truncate+reload for full
    reprocessing, or upsert for incremental. Track pipeline run IDs.
    """
    help = 'Q91 Solution: Idempotent pipeline with truncate+reload or upsert'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q91 SOLUTION: Idempotent pipeline - safe to re-run')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q91-SOL-{i:03}',
                customer_email=f'q91sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        # Pattern 1: Truncate + Reload
        self.stdout.write('Pattern 1: Truncate + Reload (full batch)')
        output_store = {}  # Use dict keyed by ID (simulates unique constraint)

        def run_pipeline_truncate_reload():
            output_store.clear()  # truncate first
            orders = list(Order.objects.values('id', 'order_number', 'amount'))
            for order in orders:
                output_store[order['id']] = {'id': order['id'], 'amount': str(order['amount'])}

        run_pipeline_truncate_reload()
        self.stdout.write(f'  Run 1: {len(output_store)} rows')
        run_pipeline_truncate_reload()
        self.stdout.write(self.style.SUCCESS(f'  Run 2: {len(output_store)} rows <- same, no duplicates'))

        # Pattern 2: Upsert (incremental)
        self.stdout.write('\nPattern 2: Upsert (incremental)')
        upsert_store = {}

        def run_pipeline_upsert():
            orders = list(Order.objects.values('id', 'order_number', 'amount'))
            for order in orders:
                upsert_store[order['id']] = {  # overwrite if exists
                    'id': order['id'], 'amount': str(order['amount'])
                }

        run_pipeline_upsert()
        self.stdout.write(f'  Run 1: {len(upsert_store)} rows')
        run_pipeline_upsert()
        self.stdout.write(self.style.SUCCESS(f'  Run 2: {len(upsert_store)} rows <- same, upserted'))

        # Pattern 3: Run ID deduplication
        self.stdout.write('\nPattern 3: Run ID tracking')
        completed_runs = set()

        def run_with_id(run_id):
            if run_id in completed_runs:
                self.stdout.write(self.style.WARNING(
                    f'  Run {run_id}: SKIPPED (already completed)'
                ))
                return
            # ... do work ...
            completed_runs.add(run_id)
            self.stdout.write(self.style.SUCCESS(f'  Run {run_id}: completed'))

        run_with_id('run-2024-01-15')
        run_with_id('run-2024-01-15')  # duplicate attempt
        run_with_id('run-2024-01-16')  # new run

        self.stdout.write('\nSQL upsert (PostgreSQL):')
        self.stdout.write('  INSERT INTO reports (order_id, amount)')
        self.stdout.write('  SELECT id, amount FROM orders')
        self.stdout.write('  ON CONFLICT (order_id)')
        self.stdout.write('  DO UPDATE SET amount = EXCLUDED.amount;')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Truncate+reload: safe for full batch pipelines')
        self.stdout.write('  - Upsert: safe for incremental pipelines')
        self.stdout.write('  - Run ID: prevent concurrent or duplicate runs')
        self.stdout.write('  - Test: run twice, assert output is identical')
