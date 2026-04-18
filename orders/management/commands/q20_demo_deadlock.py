from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q20 PROBLEM: Deadlocks occur when two transactions each hold a lock the
    other needs, forming a circular wait. Both transactions are blocked forever
    until the DB detects the deadlock and rolls back one of them.

    Common cause: two transactions lock the same rows in different orders.
    """
    help = 'Q20 Problem: Deadlock caused by inconsistent lock ordering'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q20 PROBLEM: Deadlock from inconsistent row lock ordering')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order_a = Order.objects.create(
            order_number='Q20-ORDER-A',
            customer_email='q20a@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order_b = Order.objects.create(
            order_number='Q20-ORDER-B',
            customer_email='q20b@example.com',
            amount=Decimal('200.00'),
            price=Decimal('200.00'),
        )
        self.stdout.write(f'Created Order-A (pk={order_a.pk}) and Order-B (pk={order_b.pk})')

        self.stdout.write('\nDeadlock scenario (sequential simulation):')
        self.stdout.write('  TX-1 locks Order-A first, then tries to lock Order-B')
        self.stdout.write('  TX-2 locks Order-B first, then tries to lock Order-A')
        self.stdout.write('  -> Circular wait -> Deadlock!')
        self.stdout.write('\n  In production with concurrent transactions:')
        self.stdout.write('  TX-1: SELECT ... FOR UPDATE WHERE id=A  [locks A]')
        self.stdout.write('  TX-2: SELECT ... FOR UPDATE WHERE id=B  [locks B]')
        self.stdout.write('  TX-1: SELECT ... FOR UPDATE WHERE id=B  [WAITS for TX-2]')
        self.stdout.write('  TX-2: SELECT ... FOR UPDATE WHERE id=A  [WAITS for TX-1]')
        self.stdout.write('  -> DB detects deadlock, rolls back one TX with an error')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: One transaction is aborted, the operation fails, and the '
            'application must handle and retry the rolled-back transaction.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Random 500 errors in production under load')
        self.stdout.write('  - Hard to reproduce in development (requires concurrent access)')
        self.stdout.write('  - Causes partial data updates if not handled')
