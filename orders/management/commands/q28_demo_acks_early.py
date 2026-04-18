from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q28 PROBLEM: Celery has two acknowledgment modes:
      - acks_early (default): broker acknowledges immediately after task dispatches to worker
      - acks_late: broker acknowledges only after task completes

    With acks_early, if the worker crashes, the task is lost (never retried).
    This is dangerous for critical tasks.
    """
    help = 'Q28 Problem: acks_early loses tasks on worker crash'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q28 PROBLEM: acks_early causes task loss')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # acks_early is default
        @app.task  # acks_early=True is implicit
        def vulnerable_task(order_id):
            """This task will be lost if worker crashes mid-execution."""
            self.stdout.write(f'  Received task for order {order_id}')
            # Simulate: start processing (takes time)
            # If worker crashes here, the task is already ACK'd and gone

        order = Order.objects.create(
            order_number='Q28-ORDER',
            customer_email='q28@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask execution (acks_early):')
        self.stdout.write('  [Broker] Task dispatched to worker')
        self.stdout.write('  [Broker] Immediately ACK (acknowledges task)')
        vulnerable_task(order.pk)
        self.stdout.write('  [Worker] Processing starts...')
        self.stdout.write('  [Worker] CRASH! (mid-execution)')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Task is LOST!\n'
            '  - Broker already acknowledged\n'
            '  - Task never retried\n'
            '  - No error logging or alert'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Critical tasks silently disappear')
        self.stdout.write('  - No way to know they failed')
        self.stdout.write('  - Partial state left in DB')
