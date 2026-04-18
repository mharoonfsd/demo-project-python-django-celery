from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q28 SOLUTION: Use acks_late=True to defer acknowledgment until the task
    completes successfully. If the worker crashes, the task remains in the
    queue and is retried by another worker.
    """
    help = 'Q28 Solution: acks_late ensures task retry on crash'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q28 SOLUTION: acks_late=True for reliable delivery')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(acks_late=True)  # ACK only after completion
        def reliable_task(order_id):
            """This task will be retried if worker crashes mid-execution."""
            self.stdout.write(f'  Processing order {order_id}...')
            return f'processed_{order_id}'

        order = Order.objects.create(
            order_number='Q28-SOL-ORDER',
            customer_email='q28sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask execution (acks_late=True):')
        self.stdout.write('  [Broker] Task dispatched to worker')
        self.stdout.write('  [Worker] Processing starts...')
        result = reliable_task(order.pk)
        self.stdout.write('  [Worker] Processing complete!')
        self.stdout.write('  [Broker] ACK received (task acknowledged)')

        self.stdout.write(self.style.SUCCESS(
            f'\nTask result: {result}'
        ))
        self.stdout.write('\nIf worker had crashed mid-execution:')
        self.stdout.write('  - Broker never received ACK')
        self.stdout.write('  - Task remains in queue')
        self.stdout.write('  - Another worker automatically retries')
        self.stdout.write('  - Task guaranteed to complete eventually')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use acks_late=True for critical tasks')
        self.stdout.write('  - Ensures at-least-once delivery (with idempotency)')
        self.stdout.write('  - Small performance cost for reliability guarantee')
        self.stdout.write('  - Combine with idempotency key for safety')
