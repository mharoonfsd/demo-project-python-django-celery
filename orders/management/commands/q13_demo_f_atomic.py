from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import time

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q13 PROBLEM: A Python-level read-modify-write on a numeric field is NOT
    atomic. Under concurrent load, two threads can both read the same value,
    both add to it, and both write back — resulting in one increment being lost.
    This is the classic "lost update" race condition.
    """
    help = 'Q13 Problem: Python-level read-modify-write causes lost updates under concurrency'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q13 PROBLEM: Race condition with Python-level read-modify-write')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q13-ORDER-1',
            customer_email='q13@example.com',
            amount=Decimal('0.00'),
            price=Decimal('0.00'),
        )
        self.stdout.write(f'Order created with amount={order.amount}')

        # PROBLEM: two threads both read amount=0, add 10, write 10
        # Expected final amount = 20, actual = 10 (lost update)
        def unsafe_increment(pk, increment):
            o = Order.objects.get(pk=pk)
            time.sleep(0.05)  # simulate processing delay — opens race window
            o.amount = o.amount + Decimal(str(increment))
            o.save(update_fields=['amount'])

        self.stdout.write('\nLaunching 2 concurrent threads that each add 10 to amount...')
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(unsafe_increment, order.pk, 10)
            f2 = executor.submit(unsafe_increment, order.pk, 10)
            f1.result(); f2.result()

        order.refresh_from_db()
        self.stdout.write(self.style.ERROR(
            f'\nFinal amount: {order.amount}  (expected 20.00 — lost update detected if < 20)'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - One increment is silently lost')
        self.stdout.write('  - Billing, inventory, and counters all suffer this in production')
        self.stdout.write('  - Impossible to reproduce in single-threaded tests')
