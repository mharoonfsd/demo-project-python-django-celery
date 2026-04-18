from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q8 PROBLEM: unique_together (or UniqueConstraint) prevents duplicate rows
    at the DB level, but under concurrent load two requests can both pass the
    Python-level check before either has committed, then both try to INSERT —
    one will succeed and the other raises IntegrityError.
    If this error is not handled the request crashes with a 500.
    """
    help = 'Q8 Problem: unique_together race condition causes unhandled IntegrityError'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q8 PROBLEM: unique_together race condition')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Simulate: first request creates the order
        Order.objects.create(
            order_number='Q8-DUPLICATE',
            customer_email='q8@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write('First request: Order Q8-DUPLICATE created.')

        # PROBLEM: second concurrent request does NOT handle IntegrityError
        self.stdout.write('\nSecond concurrent request attempting same order_number...')
        try:
            # No check, no retry — will raise IntegrityError
            Order.objects.create(
                order_number='Q8-DUPLICATE',
                customer_email='q8@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'IntegrityError: {e}'))
            self.stdout.write(self.style.ERROR(
                'PROBLEM: Unhandled IntegrityError crashes the request with 500 in production.'
            ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Race condition window exists between check and insert')
        self.stdout.write('  - Without error handling, users see 500 errors')
        self.stdout.write('  - Application-level uniqueness checks are NOT atomic')
