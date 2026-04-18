from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q38 PROBLEM: If task code changes (new parameter, different logic), old
    tasks enqueued with the old signature may fail or behave unexpectedly
    when executed by a worker running new code. Task versioning is not
    automatically handled.
    """
    help = 'Q38 Problem: Task version mismatch causes compatibility failures'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q38 PROBLEM: Task signature mismatch on deploy')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Simulate old task definition
        @app.task
        def process_order_v1(order_id):
            """Old task signature: only takes order_id."""
            return f'Processed {order_id}'

        order = Order.objects.create(
            order_number='Q38-ORDER',
            customer_email='q38@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nScenario:')
        self.stdout.write('Production code (V1): def process_order(order_id)')
        self.stdout.write('  -> 1000 tasks enqueued')
        self.stdout.write('')

        self.stdout.write('Code deployed to production (V2): def process_order(order_id, user_id)')
        self.stdout.write('  -> Now requires two parameters')
        self.stdout.write('')

        self.stdout.write('Worker starts executing old tasks:')
        try:
            result = process_order_v1(order.pk)
            self.stdout.write(f'  Old task with V2 code: {result}')
        except TypeError as e:
            self.stdout.write(self.style.ERROR(f'  TypeError: {e}'))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Task execution failure\n'
            '  - Worker has new code expecting user_id\n'
            '  - Old tasks in queue only have order_id\n'
            '  - Missing parameter causes exception\n'
            '  - Thousands of old tasks fail'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Silent failures on deploy')
        self.stdout.write('  - Task queue backlog grows')
        self.stdout.write('  - Rollback required to clear queue')
