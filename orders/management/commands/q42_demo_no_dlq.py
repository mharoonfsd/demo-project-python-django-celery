from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q42 PROBLEM: Without a dead letter queue (DLQ), tasks that fail permanently
    are simply dropped. There's no audit trail or way to recover them. Failed
    tasks vanish from the system.
    """
    help = 'Q42 Problem: No DLQ for failed tasks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q42 PROBLEM: Missing dead letter queue')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(bind=True, max_retries=2)
        def failing_task(self, order_id):
            """Task that always fails."""
            if self.request.retries < 2:
                raise Exception('Permanent error')

        order = Order.objects.create(
            order_number='Q42-ORDER',
            customer_email='q42@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask that fails permanently:')
        try:
            failing_task(order.pk)
        except Exception as e:
            self.stdout.write(f'  Exception: {e}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Task disappeared\n'
            '  - After max retries, task is dropped\n'
            '  - No record of what failed\n'
            '  - No way to replay or investigate\n'
            '  - Work is permanently lost'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Silent data loss')
        self.stdout.write('  - No audit trail for failed operations')
        self.stdout.write('  - Impossible to reconcile with external systems')
