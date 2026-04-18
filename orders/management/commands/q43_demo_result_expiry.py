from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q43–Q50: Key Production Patterns Summary.
    Q43: Result expiry too short - results evicted before task retrieves them
    Q44: No visibility - missing logs and metrics
    Q45: Task name collisions - multiple tasks with same name
    Q46: Memory leaks - long-running workers accumulate memory
    Q47: Signal handlers - dangerous in async context
    Q48: Task dependencies not tracked - orphaned subtasks
    Q49: No rate limiting - traffic spike kills system
    Q50: Broker persistence - tasks lost on crash
    """
    help = 'Q43: Result expires before retrieval'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q43 PROBLEM: Result backend expires too quickly')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def compute_result(order_id):
            order = Order.objects.get(pk=order_id)
            time.sleep(0.5)  # Simulate work
            return float(order.amount)

        order = Order.objects.create(
            order_number='Q43-ORDER',
            customer_email='q43@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nWith short result TTL (e.g., 10 minutes):')
        self.stdout.write('  CELERY_RESULT_EXPIRES = 600  # 10 minutes')
        self.stdout.write('')
        self.stdout.write('  12:00:00 -> Task completes, result stored')
        self.stdout.write('  12:10:01 -> Result expired and evicted')
        self.stdout.write('  12:10:05 -> Client calls task.get() -> result not found!')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Result loss\n'
            '  - Task completed successfully\n'
            '  - Result not retrievable after TTL\n'
            '  - Client has no way to know outcome'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Long-running operations lose results')
        self.stdout.write('  - Client cannot verify completion')
        self.stdout.write('  - Impossible to audit outcomes')
