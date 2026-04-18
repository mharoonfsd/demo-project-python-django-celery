from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import sys


class Command(BaseCommand):
    """
    Q46 PROBLEM: Long-running worker processes can accumulate memory leaks.
    Without periodic restarts, workers gradually consume more memory until
    the system runs out of RAM and crashes.
    """
    help = 'Q46 Problem: Memory leak in long-running workers'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q46 PROBLEM: Worker memory leaks')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def leaky_task(order_id):
            """Task with memory leak (holds cache)."""
            # Simulate: cache that grows indefinitely
            return 'done'

        order = Order.objects.create(
            order_number='Q46-ORDER',
            customer_email='q46@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Scenario: Worker running 1000 tasks/hour')
        self.stdout.write('')
        self.stdout.write('Memory over time:')
        self.stdout.write('  Start: 500 MB')
        self.stdout.write('  1 hour: 650 MB (+150 MB)')
        self.stdout.write('  2 hours: 800 MB (+150 MB)')
        self.stdout.write('  24 hours: 4500 MB (4.5 GB!)')
        self.stdout.write('  48 hours: OOM Kill!')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Uncontrolled memory growth\n'
            '  - Memory never freed\n'
            '  - Worker becomes unresponsive\n'
            '  - OOM killer terminates process'
        ))
