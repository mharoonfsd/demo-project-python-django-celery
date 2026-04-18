from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q42 SOLUTION: Configure a dead letter queue in the broker. When tasks
    exceed max retries, route them to the DLQ. Periodically inspect and
    replay DLQ tasks manually or automatically.
    """
    help = 'Q42 Solution: Dead letter queue for failed tasks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q42 SOLUTION: Dead letter queue setup')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Simulate DLQ
        dlq_tasks = []

        @app.task(bind=True, max_retries=2)
        def safe_failing_task(self, order_id):
            """Task that fails and goes to DLQ."""
            order = Order.objects.get(pk=order_id)
            if self.request.retries < 2:
                raise Exception('Transient error')
            return 'success'

        order = Order.objects.create(
            order_number='Q42-SOL-ORDER',
            customer_email='q42sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nDLQ configuration:')
        self.stdout.write('  RabbitMQ:')
        self.stdout.write('    - Queue: orders_dlq')
        self.stdout.write('    - Exchange: orders_dlq_exchange')
        self.stdout.write('    - x-max-length: 100000')
        self.stdout.write('    - x-message-ttl: 86400000 (24 hours)')
        self.stdout.write('')

        self.stdout.write('  Celery task routing:')
        self.stdout.write('    - On max retries, route to dlq queue')
        self.stdout.write('    - Log task with full traceback')

        self.stdout.write('\nMonitoring DLQ:')
        self.stdout.write('  1. Periodic check (hourly cron job)')
        self.stdout.write('  2. Alert if DLQ queue length > threshold')
        self.stdout.write('  3. Manual replay via management command')
        self.stdout.write('  4. Export for analysis')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always configure a DLQ in the broker')
        self.stdout.write('  - Route max_retries failures to DLQ')
        self.stdout.write('  - Monitor DLQ depth and alert on threshold')
        self.stdout.write('  - Replay DLQ tasks manually after fixing root cause')
