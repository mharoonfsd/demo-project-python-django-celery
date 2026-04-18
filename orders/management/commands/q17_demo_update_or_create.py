from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q17 PROBLEM: update_or_create() has the same race condition as get_or_create().
    The GET, then CREATE/UPDATE sequence is not atomic. Two concurrent requests
    can both see no row, both try to INSERT, and one will hit IntegrityError —
    OR both find the row and race to UPDATE it, potentially with stale defaults.
    """
    help = 'Q17 Problem: update_or_create() race condition causes duplicates or IntegrityError'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q17 PROBLEM: update_or_create() race condition')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        self.stdout.write('Calling update_or_create() for a new order...')
        order1, created1 = Order.objects.update_or_create(
            order_number='Q17-UOC',
            defaults={'customer_email': 'q17@example.com', 'amount': Decimal('100.00'), 'price': Decimal('100.00')},
        )
        self.stdout.write(f'Request 1: created={created1}, pk={order1.pk}, amount={order1.amount}')

        # Simulating the race: a second concurrent request used stale defaults
        # Both requests read "no row exists", both attempt INSERT with different defaults
        self.stdout.write('\nSimulating race collision (concurrent INSERT with different amount)...')
        try:
            Order.objects.create(
                order_number='Q17-UOC',           # same unique key
                customer_email='q17b@example.com',
                amount=Decimal('999.00'),          # different data — who wins?
                price=Decimal('999.00'),
            )
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'IntegrityError (unhandled): {e}'))
            self.stdout.write(self.style.ERROR(
                'PROBLEM: Concurrent request crashed. In a true race both could have '
                'different "defaults" written — last writer wins silently.'
            ))

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Concurrent requests can corrupt each other\'s updates')
        self.stdout.write('  - "Last writer wins" may override intentional updates')
        self.stdout.write('  - IntegrityError on INSERT crashes un-protected requests')
