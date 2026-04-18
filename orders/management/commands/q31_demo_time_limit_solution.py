from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q31 SOLUTION: Use soft_time_limit before hard time_limit. soft_time_limit
    raises SoftTimeLimitExceeded exception, allowing cleanup code to run before
    the hard kill. Set hard time_limit 10-20s higher than soft_time_limit.
    """
    help = 'Q31 Solution: Use soft_time_limit with cleanup handler'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q31 SOLUTION: soft_time_limit with cleanup')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(
            soft_time_limit=5,    # Raise exception at 5s
            time_limit=10         # Hard kill at 10s
        )
        def safe_task(order_id):
            """Task with graceful timeout handling via try/except."""
            # In production (Linux workers), Celery raises SoftTimeLimitExceeded.
            # Here we simulate the same flow for demo purposes.
            self.stdout.write('  Task started...')
            try:
                for i in range(3):
                    self.stdout.write(f'    Working (step {i+1}/3)...')
                return 'done'
            except Exception as e:
                self.stdout.write(self.style.WARNING('  -> Soft timeout! Cleaning up...'))
                self.stdout.write('    - Closing DB connections')
                self.stdout.write('    - Flushing buffers')
                self.stdout.write('    - Logging state')
                return 'failed_but_cleaned_up'

        order = Order.objects.create(
            order_number='Q31-SOL-ORDER',
            customer_email='q31sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask execution with soft_time_limit:')
        result = safe_task(order.pk)
        self.stdout.write(self.style.SUCCESS(f'Result: {result}'))

        self.stdout.write('\nTimeout handling sequence:')
        self.stdout.write('  5s: soft_time_limit triggers, raises exception')
        self.stdout.write('  -> Exception caught, cleanup runs')
        self.stdout.write('  -> Task completes gracefully')
        self.stdout.write('  10s: hard time_limit (unused if soft cleanup worked)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use soft_time_limit < time_limit')
        self.stdout.write('  - Catch TimeLimitExceeded and clean up')
        self.stdout.write('  - Set hard time_limit 10-30% higher than soft')
        self.stdout.write('  - Test timeout scenarios in development')
