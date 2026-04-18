from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q29 PROBLEM: The retry() method reschedules a task for later execution.
    However, exponential backoff with retries can delay critical tasks
    indefinitely, especially if all retries fail.
    """
    help = 'Q29 Problem: Retry with exponential backoff delays critical tasks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q29 PROBLEM: Exponential backoff delays tasks')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        retry_count = [0]

        @app.task(bind=True, max_retries=4)
        def flaky_task(self, order_id):
            """Task that fails intermittently and retries with exponential backoff."""
            retry_count[0] += 1
            self.stdout.write(f'  Attempt {retry_count[0]}...')

            if retry_count[0] < 4:
                self.stdout.write(f'    -> Failed, retrying...')
                # Exponential backoff: 2^retry_count seconds
                countdown = 2 ** (self.request.retries - 1) if self.request.retries > 0 else 2
                raise self.retry(countdown=countdown, exc=Exception('Temporary failure'))

            self.stdout.write(f'    -> Success!')
            return 'done'

        order = Order.objects.create(
            order_number='Q29-ORDER',
            customer_email='q29@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask with exponential backoff:')
        try:
            flaky_task(order.pk)
        except Exception as e:
            self.stdout.write(f'  Exception: {e}')

        self.stdout.write(self.style.WARNING(
            '\nPROBLEM: Retry schedule:\n'
            '  Attempt 1: immediate\n'
            '  Attempt 2: +2s (2s after start)\n'
            '  Attempt 3: +4s (6s after start)\n'
            '  Attempt 4: +8s (14s after start)\n'
            'Total delay for critical task: 14+ seconds!'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Critical operations delayed by growing intervals')
        self.stdout.write('  - If all retries fail, no alerting')
        self.stdout.write('  - Customer impact increases with retry count')
