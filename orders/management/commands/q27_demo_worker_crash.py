from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q27 PROBLEM: If a Celery worker crashes mid-task (before completing),
    the task is requeued by the broker. The task runs again on another worker.
    Without crash detection, this can cause partial state changes or duplicates.
    """
    help = 'Q27 Problem: Worker crash mid-task causes requeue without cleanup'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q27 PROBLEM: Worker crash causes task requeue')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def process_order(order_id):
            """
            Multi-step task that can crash mid-way:
            1. Debit customer
            2. CRASH HERE
            3. Ship items
            """
            order = Order.objects.get(pk=order_id)
            self.stdout.write(f'  [Step 1] Debiting ${order.amount}...')
            # Simulate debit
            order.amount = order.amount - Decimal('10.00')
            order.save()

            self.stdout.write(f'  [Step 2] WORKER CRASH! (mid-process)')
            raise Exception('Worker killed (OOM, SIGKILL)')

            # Step 3 never runs
            self.stdout.write(f'  [Step 3] Shipping items...')

        order = Order.objects.create(
            order_number='Q27-ORDER',
            customer_email='q27@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask execution:')
        try:
            process_order(order.pk)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Exception: {e}'))

        order.refresh_from_db()
        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Order partially processed!\n'
            f'  Amount was debited ({order.amount})\n'
            f'  But items were NOT shipped (Step 3 skipped)\n'
            f'  Broker will requeue and likely duplicate the debit!'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Partial state: customer charged but not fulfilled')
        self.stdout.write('  - Requeue causes duplicate charge attempts')
        self.stdout.write('  - No way to rollback partial changes')
