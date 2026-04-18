from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
from datetime import datetime, timedelta


class Command(BaseCommand):
    """
    Q30 PROBLEM: When using countdown (e.g., retry(countdown=60)), the delay
    is relative to the worker's local clock. If two workers have different
    system times (clock skew), tasks can be scheduled inconsistently or run
    out of order.
    """
    help = 'Q30 Problem: Countdown drift from clock skew between workers'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q30 PROBLEM: Clock skew causes countdown drift')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(bind=True, max_retries=2)
        def drifting_task(self, order_id):
            """Task scheduled with countdown (relative delay)."""
            self.stdout.write(f'  Current time: {datetime.now().isoformat()}')
            if self.request.retries == 0:
                self.stdout.write(f'  First attempt, retrying in 60s')
                raise self.retry(countdown=60, exc=Exception('Retry'))
            return 'done'

        order = Order.objects.create(
            order_number='Q30-ORDER',
            customer_email='q30@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nScenario: two workers with different system clocks')
        self.stdout.write('Worker-A clock: 10:00:00 AM')
        self.stdout.write('Worker-B clock: 10:01:30 AM (90s ahead)')
        self.stdout.write('')

        self.stdout.write('Worker-A schedules task retry for 10:01:00 (60s later)')
        self.stdout.write('Worker-B sees ETA: 10:01:00, but its clock is 10:01:30')
        self.stdout.write('Result: Task executes immediately (or in the past!) on Worker-B')

        self.stdout.write(self.style.WARNING(
            '\nPROBLEM: Countdown drift causes:\n'
            '  - Tasks run earlier/later than intended\n'
            '  - Retries trigger out-of-order\n'
            '  - Rate limiting fails\n'
            '  - Timeouts miscalculated'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Unpredictable task scheduling')
        self.stdout.write('  - Retry storms if many workers have skew')
        self.stdout.write('  - Hard to debug (depends on server config)')
