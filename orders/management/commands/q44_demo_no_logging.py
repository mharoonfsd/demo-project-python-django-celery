from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q44 PROBLEM: Without proper logging and monitoring, it's impossible to
    diagnose issues. Task failures, retries, and slowdowns go unnoticed.
    """
    help = 'Q44 Problem: Missing observability and logging'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q44 PROBLEM: No observability/logging')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def opaque_task(order_id):
            """Task with no logging."""
            return 'done'

        order = Order.objects.create(
            order_number='Q44-ORDER',
            customer_email='q44@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Task runs, but what happens inside?')
        self.stdout.write('  - No log statements')
        self.stdout.write('  - No metrics emitted')
        self.stdout.write('  - Silent failures')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Black box operation\n'
            '  - Can\'t debug issues\n'
            '  - Can\'t detect slowdowns\n'
            '  - No visibility into failures'
        ))
