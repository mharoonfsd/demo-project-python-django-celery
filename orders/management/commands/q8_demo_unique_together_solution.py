from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q8 SOLUTION: Catch IntegrityError at the call site and fall back to
    get() to retrieve the existing record. This is the standard
    "optimistic insert" pattern — try to insert, handle the rare collision.
    Always rely on DB-level unique constraints as the source of truth.
    """
    help = 'Q8 Solution: Handle IntegrityError with get_or_create + graceful fallback'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q8 SOLUTION: Graceful handling of unique_together race condition')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        def safe_get_or_create_order(order_number, email, amount):
            """
            Optimistic insert pattern: try create(), catch IntegrityError,
            fall back to get(). Thread-safe and race-condition-proof.
            """
            try:
                order, created = Order.objects.get_or_create(
                    order_number=order_number,
                    defaults={'customer_email': email, 'amount': amount, 'price': amount},
                )
                return order, created
            except IntegrityError:
                # Race condition: another process beat us to it — just fetch it
                order = Order.objects.get(order_number=order_number)
                return order, False

        # First request
        order1, created1 = safe_get_or_create_order('Q8-DUPLICATE', 'q8@example.com', Decimal('100.00'))
        self.stdout.write(f'First request: created={created1}, pk={order1.pk}')

        # Second concurrent request — no crash, gets existing record
        order2, created2 = safe_get_or_create_order('Q8-DUPLICATE', 'q8@example.com', Decimal('100.00'))
        self.stdout.write(f'Second request: created={created2}, pk={order2.pk}')

        self.stdout.write(self.style.SUCCESS('\nNo crash! Both requests handled gracefully.'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use get_or_create() instead of manual check-then-insert')
        self.stdout.write('  - Wrap in try/except IntegrityError for extra safety in concurrent scenarios')
        self.stdout.write('  - DB-level unique constraint is the real guard; application logic is secondary')
