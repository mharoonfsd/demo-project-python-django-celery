from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q32 PROBLEM: Without idempotency, duplicate task executions cause errors.
    Tasks should be designed to produce the same result regardless of how many
    times they run. This requires an idempotency key stored in the DB.
    """
    help = 'Q32 Problem: Non-idempotent tasks fail on duplicate execution'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q32 PROBLEM: Non-idempotent task design')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def non_idempotent_increment(order_id):
            """Increments counter — duplicates cause wrong total."""
            order = Order.objects.get(pk=order_id)
            # BUG: No idempotency — just blindly increment
            order.amount = order.amount + Decimal('10.00')
            order.save()
            self.stdout.write(f'  Incremented amount to {order.amount}')
            return float(order.amount)

        order = Order.objects.create(
            order_number='Q32-ORDER',
            customer_email='q32@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk} with amount=100.00')

        self.stdout.write('\nRunning task:')
        non_idempotent_increment(order.pk)
        order.refresh_from_db()
        self.stdout.write(f'After run 1: amount={order.amount}')

        self.stdout.write('\nRunning same task again (duplicate/retry):')
        non_idempotent_increment(order.pk)
        order.refresh_from_db()
        self.stdout.write(f'After run 2: amount={order.amount}')

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Amount is {order.amount}, should be 100.00!\n'
            '  - First execution: 100 -> 110\n'
            '  - Duplicate execution: 110 -> 120\n'
            '  - Each retry multiplies the effect'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Duplicate tasks corrupt data')
        self.stdout.write('  - Side effects repeat multiple times')
        self.stdout.write('  - Hard to detect after-the-fact')
