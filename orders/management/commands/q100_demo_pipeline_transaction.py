from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q100 PROBLEM: Multi-step pipeline copies data between tables without
    using database transactions. A crash between steps leaves the DB in
    a half-migrated state. Running the pipeline again causes duplicates
    or errors because partial work was already done.
    """
    help = 'Q100 Problem: Pipeline steps not in transaction - crash = inconsistent DB'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q100 PROBLEM: Non-transactional pipeline - crash = inconsistent state')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q100-ORD-{i:03}',
                customer_email=f'q100user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        processed_log = []

        def step_1_process_orders():
            """Step 1: Mark orders as processing."""
            orders = list(Order.objects.values('id', 'order_number'))
            for order in orders:
                processed_log.append(order['id'])
            return orders

        def step_2_crash_midway(orders):
            """Step 2: Crashes after processing some orders."""
            for i, order in enumerate(orders):
                if i == 3:  # Crash after 3 orders
                    raise RuntimeError('Container OOM killed at step 2')
                # Some irreversible side effect (e.g., external API call)
                pass

        self.stdout.write('Pipeline run (will crash at step 2):')
        self.stdout.write('  Step 1: Processing...')
        orders = step_1_process_orders()
        self.stdout.write(self.style.SUCCESS(f'  Step 1: {len(orders)} orders processed'))
        self.stdout.write(f'  Processed log: {processed_log}')

        self.stdout.write('  Step 2: Applying changes...')
        try:
            step_2_crash_midway(orders)
        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(f'  CRASH: {e}'))
            self.stdout.write(self.style.ERROR(
                f'  processed_log has {len(processed_log)} entries (step 1 completed)'
                f'\n  DB state is partially modified'
                f'\n  Re-running pipeline: step 1 processes all 5 again -> duplicates in log'
            ))

        # Re-run scenario
        step_1_process_orders()
        self.stdout.write(self.style.ERROR(
            f'\n  After re-run: processed_log = {processed_log}'
            f'\n  Orders 1-5 appear TWICE in the log!'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No transaction wraps multi-step pipeline'
            '\n  - Crash between steps = partial state in DB'
            '\n  - Re-run causes duplicates in already-processed records'
            '\n  - Manual cleanup required before re-running'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Wrap multi-step DB operations in transaction.atomic()')
        self.stdout.write('  - Crash rolls back all changes atomically')
        self.stdout.write('  - Idempotent steps: check-then-act, not blind-act')
        self.stdout.write('  - External API calls cannot be rolled back -> use saga pattern')
