from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q9 SOLUTION: Use transaction.atomic() with savepoint=True (the default)
    for inner blocks. When the inner block fails and is rolled back, the outer
    transaction continues cleanly from the savepoint — no poisoning.
    The key insight: the inner atomic() already creates a savepoint by default,
    but the outer TX still needs the inner exception to be handled BEFORE the
    inner atomic() context manager exits cleanly (no re-raise).
    """
    help = 'Q9 Solution: Use savepoints so inner failure does not break outer transaction'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q9 SOLUTION: Savepoints isolate inner failures')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        with transaction.atomic():  # outer block
            Order.objects.create(
                order_number='Q9-SOL-OUTER',
                customer_email='q9outer@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            self.stdout.write('Outer: created Q9-SOL-OUTER')

            # SOLUTION: inner atomic() uses a DB savepoint automatically.
            # If the inner block raises and we catch it OUTSIDE the inner atomic(),
            # the savepoint is rolled back but the outer TX remains intact.
            try:
                with transaction.atomic():  # creates SAVEPOINT
                    Order.objects.create(
                        order_number='Q9-SOL-INNER',
                        customer_email='q9inner@example.com',
                        amount=Decimal('50.00'),
                        price=Decimal('50.00'),
                    )
                    raise ValueError('Simulated inner failure')  # rolled back to savepoint
            except ValueError as e:
                self.stdout.write(self.style.WARNING(f'Inner exception caught (savepoint rolled back): {e}'))
                self.stdout.write('  Outer transaction is still alive!')

            # Outer block can still write
            Order.objects.create(
                order_number='Q9-SOL-AFTER',
                customer_email='q9after@example.com',
                amount=Decimal('75.00'),
                price=Decimal('75.00'),
            )
            self.stdout.write('Outer: created Q9-SOL-AFTER successfully')

        count = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\nOrders in DB: {count}  (outer + after order saved)'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Inner atomic() blocks create DB savepoints automatically')
        self.stdout.write('  - A failed inner block rolls back only to the savepoint')
        self.stdout.write('  - Catch inner exceptions outside the inner atomic() block to keep outer TX healthy')
        self.stdout.write('  - Q9-SOL-INNER should NOT be in DB (rolled back); Q9-SOL-OUTER and Q9-SOL-AFTER should be')
