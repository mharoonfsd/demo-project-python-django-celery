from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q20 SOLUTION: Prevent deadlocks by always acquiring locks in a consistent
    order (e.g., ascending primary key). When all code locks rows in the same
    order, circular waits are impossible.

    Additional strategies: reduce lock scope, use NOWAIT/SKIP LOCKED, and
    implement retry logic for any remaining deadlock errors.
    """
    help = 'Q20 Solution: Prevent deadlocks with consistent lock ordering'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q20 SOLUTION: Consistent lock ordering prevents deadlocks')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order_a = Order.objects.create(
            order_number='Q20-SOL-ORDER-A',
            customer_email='q20sola@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order_b = Order.objects.create(
            order_number='Q20-SOL-ORDER-B',
            customer_email='q20solb@example.com',
            amount=Decimal('200.00'),
            price=Decimal('200.00'),
        )
        self.stdout.write(f'Created Order-A (pk={order_a.pk}) and Order-B (pk={order_b.pk})')

        def safe_lock_and_update(order_ids, increment):
            """Always lock rows in ascending PK order to prevent deadlocks."""
            sorted_ids = sorted(order_ids)  # CRITICAL: consistent order
            with transaction.atomic():
                orders = list(
                    Order.objects.select_for_update().filter(
                        pk__in=sorted_ids
                    ).order_by('pk')   # enforce same order in the actual SQL
                )
                for order in orders:
                    order.amount += Decimal(str(increment))
                    order.save(update_fields=['amount'])
                return orders

        # TX-1 and TX-2 both acquire locks in ascending PK order — no deadlock
        self.stdout.write('\nTX-1 locks [Order-A, Order-B] in ascending PK order')
        results = safe_lock_and_update([order_a.pk, order_b.pk], '10.00')
        self.stdout.write(self.style.SUCCESS('TX-1 completed without deadlock'))

        self.stdout.write('\nTX-2 locks [Order-B, Order-A] — sorted to ascending PK order')
        results2 = safe_lock_and_update([order_b.pk, order_a.pk], '20.00')
        self.stdout.write(self.style.SUCCESS('TX-2 completed without deadlock'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always acquire locks on multiple rows in a deterministic order (e.g., pk ASC)')
        self.stdout.write('  - Use .order_by("pk") with select_for_update() to enforce ordering')
        self.stdout.write('  - Add retry logic for any remaining deadlock errors (OperationalError)')
        self.stdout.write('  - Use SELECT ... FOR UPDATE SKIP LOCKED for queue-style workloads')
