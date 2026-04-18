from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q100 SOLUTION: Wrap multi-step pipeline in transaction.atomic().
    Crash rolls back all DB changes. For external API calls, use saga
    pattern with compensating transactions.
    """
    help = 'Q100 Solution: Transactional pipeline with atomic multi-step operations'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q100 SOLUTION: transaction.atomic() ensures all-or-nothing')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q100-SOL-{i:03}',
                customer_email=f'q100sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        # Pattern 1: transaction.atomic() wraps all steps
        self.stdout.write('Pattern 1: Multi-step pipeline in transaction.atomic()')
        orders_before = Order.objects.count()

        try:
            with transaction.atomic():
                # Step 1: Read and process
                orders = list(Order.objects.values('id', 'amount'))
                self.stdout.write(self.style.SUCCESS(
                    f'  Step 1: {len(orders)} orders read within transaction'
                ))

                # Step 2: Update records
                for order in orders:
                    Order.objects.filter(pk=order['id']).update(
                        total=order['amount']
                    )
                self.stdout.write(self.style.SUCCESS(
                    f'  Step 2: {len(orders)} orders updated'
                ))

                # Step 3: Verify then commit
                updated = Order.objects.filter(total__isnull=False).count()
                if updated != len(orders):
                    raise ValueError(f'Expected {len(orders)} updates, got {updated}')
                self.stdout.write(self.style.SUCCESS(
                    f'  Step 3: Verification passed -> committing'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Transaction rolled back: {e}'))

        orders_after = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'  Orders before: {orders_before}, after: {orders_after} (no change to count)'
        ))

        # Pattern 2: Demonstrate rollback on failure
        self.stdout.write('\nPattern 2: Rollback demonstration')
        original_first = Order.objects.order_by('id').first()
        try:
            with transaction.atomic():
                Order.objects.filter(pk=original_first.pk).update(
                    customer_email='changed@example.com'
                )
                raise RuntimeError('Simulated crash after partial update')
        except RuntimeError:
            pass

        after_rollback = Order.objects.get(pk=original_first.pk)
        if after_rollback.customer_email == original_first.customer_email:
            self.stdout.write(self.style.SUCCESS(
                f'  Rollback worked: email is still "{after_rollback.customer_email}"'
            ))

        # Pattern 3: Saga for external API calls
        self.stdout.write('\nPattern 3: Saga pattern for external APIs (cannot roll back)')
        self.stdout.write('  Step 1: charge_card(order_id)  -> external, irreversible')
        self.stdout.write('  Step 2: reserve_inventory(order_id) -> DB, reversible')
        self.stdout.write('')
        self.stdout.write('  If Step 2 fails:')
        self.stdout.write('    Compensating transaction: refund_card(order_id)')
        self.stdout.write('    -> explicitly undo Step 1')
        self.stdout.write('')
        self.stdout.write('  def process_order_saga(order_id):')
        self.stdout.write('      payment_id = charge_card(order_id)')
        self.stdout.write('      try:')
        self.stdout.write('          reserve_inventory(order_id)  # DB transaction')
        self.stdout.write('      except Exception:')
        self.stdout.write('          refund_card(payment_id)  # compensate')
        self.stdout.write('          raise')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - transaction.atomic(): DB operations are all-or-nothing')
        self.stdout.write('  - Crash in transaction: all changes rolled back automatically')
        self.stdout.write('  - Idempotent re-runs: no duplicate data after crash+retry')
        self.stdout.write('  - External APIs (Stripe, SNS): saga pattern with compensation')
