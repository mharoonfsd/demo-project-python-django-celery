from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q50 PROBLEM: If Redis broker crashes and is not persistent, all tasks
    in the queue are lost. No durability guarantees. Tasks simply disappear
    on broker restart.
    """
    help = 'Q50 Problem: No broker persistence'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q50 PROBLEM: Non-persistent broker')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def process_order(order_id):
            return 'processed'

        order = Order.objects.create(
            order_number='Q50-ORDER',
            customer_email='q50@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Scenario: 5000 tasks in Redis queue')
        self.stdout.write('')
        self.stdout.write('What happens during broker crash:')
        self.stdout.write('  - Redis instance goes down')
        self.stdout.write('  - No persistence (appendonly: no)')
        self.stdout.write('  - 5000 tasks vanish from memory')
        self.stdout.write('  - Broker restarts, queue is empty')
        self.stdout.write('  - Tasks never execute')
        self.stdout.write('  - Orders left in pending state')
        self.stdout.write('  - Charges not processed')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Complete data loss\n'
            '  - Tasks silently lost\n'
            '  - No audit trail\n'
            '  - Difficult to recover'
        ))
