from decimal import Decimal
from django.core.management.base import BaseCommand
from celery import chain, chord
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q48 SOLUTION: Use chain() for sequential execution with error handling.
    Track task hierarchy in DB. Link tasks with task IDs and status.
    """
    help = 'Q48 Solution: Tracked task dependencies'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q48 SOLUTION: Task chains with tracking')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def validate_order(order_id):
            return True

        @app.task
        def process_payment(order_id, validation_result):
            if not validation_result:
                raise ValueError('Validation failed')
            return 'charged'

        @app.task
        def send_confirmation(order_id, payment_result):
            return 'sent'

        order = Order.objects.create(
            order_number='Q48-SOL-ORDER',
            customer_email='q48sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Solution 1: Use chain()')
        self.stdout.write('  workflow = chain(')
        self.stdout.write('      validate_order.s(order_id),')
        self.stdout.write('      process_payment.s(order_id),')
        self.stdout.write('      send_confirmation.s(order_id),')
        self.stdout.write('  )')
        self.stdout.write('  result = workflow.apply_async()')
        self.stdout.write('')
        self.stdout.write('Solution 2: Create TaskDependency model')
        self.stdout.write('  - Track parent_task_id, child_task_id, status')
        self.stdout.write('  - Child only runs if parent succeeded')
        self.stdout.write('  - Update status as tasks complete')
        self.stdout.write('')
        self.stdout.write('Solution 3: Use chord for fan-out + aggregation')
        self.stdout.write('  - Parallel tasks with shared callback')
        self.stdout.write('  - Callback waits for all children')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use chain() for sequential flows')
        self.stdout.write('  - Track task IDs in database')
        self.stdout.write('  - Monitor parent/child status')
        self.stdout.write('  - Handle cascading failures')
