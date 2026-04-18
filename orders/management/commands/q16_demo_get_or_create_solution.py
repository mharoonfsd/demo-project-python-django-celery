from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q16 SOLUTION: Wrap get_or_create() in try/except IntegrityError and
    fall back to get(). This is the standard "optimistic insert" pattern —
    attempt to create, handle the rare race collision gracefully.
    """
    help = 'Q16 Solution: Wrap get_or_create() with IntegrityError fallback'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q16 SOLUTION: Safe get_or_create() with fallback')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        def safe_get_or_create(order_number, email, amount):
            """
            Race-safe get_or_create pattern.
            Try to create; if another process beat us, just get the existing row.
            """
            try:
                return Order.objects.get_or_create(
                    order_number=order_number,
                    defaults={'customer_email': email, 'amount': amount, 'price': amount},
                )
            except IntegrityError:
                # Another concurrent process created the row between our GET and INSERT
                return Order.objects.get(order_number=order_number), False

        # Request 1
        order1, created1 = safe_get_or_create('Q16-SOL-RACE', 'q16sol@example.com', Decimal('100.00'))
        self.stdout.write(f'Request 1: created={created1}, pk={order1.pk}')

        # Request 2 — simulates the race collision, falls back gracefully
        order2, created2 = safe_get_or_create('Q16-SOL-RACE', 'q16sol@example.com', Decimal('100.00'))
        self.stdout.write(f'Request 2: created={created2}, pk={order2.pk}')

        self.stdout.write(self.style.SUCCESS('\nBoth requests handled gracefully — no 500 error.'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always wrap get_or_create() in try/except IntegrityError')
        self.stdout.write('  - The fallback get() is safe because the row is guaranteed to exist after IntegrityError')
        self.stdout.write('  - DB unique constraint is your last line of defence — never skip it')
