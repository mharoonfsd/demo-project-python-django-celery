from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q31 PROBLEM: Celery's time_limit is a hard timeout that kills the task
    process. If a task exceeds the time limit (e.g., database query hangs),
    the worker process is terminated, leaving partial state and no chance
    for cleanup.
    """
    help = 'Q31 Problem: Hard time_limit kills task process without cleanup'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q31 PROBLEM: time_limit causes hard kill')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(time_limit=5)  # Hard kill after 5 seconds
        def slow_task(order_id):
            """Task that runs for 10 seconds, exceeds 5s time_limit."""
            self.stdout.write('  Task started...')
            try:
                for i in range(10):
                    self.stdout.write(f'    Working (step {i+1}/10)...')
                    time.sleep(1)
                return 'done'
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Exception during cleanup: {e}'))
                raise

        order = Order.objects.create(
            order_number='Q31-ORDER',
            customer_email='q31@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask execution:')
        try:
            slow_task(order.pk)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  {type(e).__name__}: {e}'))

        self.stdout.write(self.style.WARNING(
            '\nPROBLEM: time_limit exceeded\n'
            '  - Task killed after 5 seconds\n'
            '  - Process terminated forcefully\n'
            '  - Cleanup code never runs\n'
            '  - DB connections left open\n'
            '  - Partial data may be left on disk'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Resource leaks (file handles, DB connections)')
        self.stdout.write('  - Partial state impossible to recover')
        self.stdout.write('  - Worker may crash or become unstable')
