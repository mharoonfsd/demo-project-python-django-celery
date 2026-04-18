from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q16 PROBLEM: get_or_create() is NOT atomic. Under concurrent load, two
    processes can both attempt the GET, both find nothing, both try the CREATE,
    and one of them will hit an IntegrityError. If this is not handled, one
    request crashes with a 500.
    """
    help = 'Q16 Problem: get_or_create() race condition causes IntegrityError'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q16 PROBLEM: get_or_create() race condition')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Simulate concurrent requests: both call get_or_create at "the same time"
        # We simulate this by manually replicating what get_or_create does internally

        self.stdout.write('Simulating two concurrent get_or_create calls for the same order_number...')

        # Request 1 succeeds
        order1, created1 = Order.objects.get_or_create(
            order_number='Q16-RACE',
            defaults={'customer_email': 'q16@example.com', 'amount': Decimal('100.00'), 'price': Decimal('100.00')},
        )
        self.stdout.write(f'Request 1: created={created1}, pk={order1.pk}')

        # Request 2: row now exists, get_or_create normally returns it
        # But in a true race, BOTH requests GET nothing simultaneously, then both INSERT
        # We simulate that collision manually:
        self.stdout.write('\nSimulating race collision (both saw empty, both try INSERT)...')
        try:
            # Force INSERT of duplicate to mimic the collision
            Order.objects.create(
                order_number='Q16-RACE',
                customer_email='q16@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'IntegrityError (unhandled): {e}'))
            self.stdout.write(self.style.ERROR(
                'PROBLEM: Request 2 crashed with IntegrityError. User sees 500.'
            ))

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Small but real race window between GET and INSERT in get_or_create()')
        self.stdout.write('  - One concurrent request will crash unless IntegrityError is caught')
        self.stdout.write('  - Becomes more likely under high concurrency or with slow DB responses')
