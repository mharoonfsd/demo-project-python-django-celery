from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

from django.core.management.base import BaseCommand
from django.db.models import F

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q13 SOLUTION: Use Django's F() expression to perform the increment
    entirely inside the database in a single atomic SQL statement.
    F() translates to "UPDATE orders_order SET amount = amount + 10 WHERE id=?"
    — the DB engine handles atomicity, no Python-level race possible.
    """
    help = 'Q13 Solution: Use F() for atomic DB-level increments to prevent lost updates'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q13 SOLUTION: F() expression for atomic updates')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q13-SOL-ORDER-1',
            customer_email='q13sol@example.com',
            amount=Decimal('0.00'),
            price=Decimal('0.00'),
        )
        self.stdout.write(f'Order created with amount={order.amount}')

        # SOLUTION: F() expression — atomic at the DB level
        def safe_increment(pk, increment):
            Order.objects.filter(pk=pk).update(
                amount=F('amount') + Decimal(str(increment))
            )

        self.stdout.write('\nLaunching 2 concurrent threads that each atomically add 10 to amount...')
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(safe_increment, order.pk, 10)
            f2 = executor.submit(safe_increment, order.pk, 10)
            f1.result(); f2.result()

        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'\nFinal amount: {order.amount}  (expected 20.00 — no lost update)'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - F() translates to a single atomic SQL UPDATE')
        self.stdout.write('  - No Python read — no race window — no lost updates')
        self.stdout.write('  - Essential for counters, balances, inventory, and any numeric field under load')
        self.stdout.write('  - Remember to call refresh_from_db() if you need the new value in Python')
