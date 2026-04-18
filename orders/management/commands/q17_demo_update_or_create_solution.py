from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q17 SOLUTION: Combine update_or_create() with select_for_update() inside
    an atomic block to serialise concurrent access, OR catch IntegrityError
    and fall back to get(). For idempotent updates, use F() expressions
    rather than overwriting with stale Python values.
    """
    help = 'Q17 Solution: Safe update_or_create() with select_for_update() or IntegrityError fallback'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q17 SOLUTION: Safe update_or_create()')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        def safe_update_or_create(order_number, email, amount):
            """
            Atomic pattern: lock the row (if it exists) before reading/writing.
            Falls back to IntegrityError catch for the first-ever insert race.
            """
            try:
                with transaction.atomic():
                    # select_for_update prevents concurrent UPDATE races on existing rows
                    existing = Order.objects.select_for_update().filter(
                        order_number=order_number
                    ).first()

                    if existing:
                        existing.amount = amount
                        existing.save(update_fields=['amount'])
                        return existing, False
                    else:
                        return Order.objects.create(
                            order_number=order_number,
                            customer_email=email,
                            amount=amount,
                            price=amount,
                        ), True
            except IntegrityError:
                # Concurrent INSERT won the race; just fetch the winner
                return Order.objects.get(order_number=order_number), False

        order1, c1 = safe_update_or_create('Q17-SOL-UOC', 'q17sol@example.com', Decimal('100.00'))
        self.stdout.write(f'Request 1: created={c1}, pk={order1.pk}, amount={order1.amount}')

        order2, c2 = safe_update_or_create('Q17-SOL-UOC', 'q17sol@example.com', Decimal('200.00'))
        self.stdout.write(f'Request 2: created={c2}, pk={order2.pk}, amount={order2.amount}')

        self.stdout.write(self.style.SUCCESS('\nNo crash. Updates serialised correctly.'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - select_for_update() inside atomic() serialises concurrent updates')
        self.stdout.write('  - Always handle IntegrityError for the first-insert race window')
        self.stdout.write('  - Use F() expressions in defaults to avoid overwriting with stale values')
