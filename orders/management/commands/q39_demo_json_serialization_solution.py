from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
from datetime import datetime
import json


class Command(BaseCommand):
    """
    Q39 SOLUTION: Either convert to JSON-serializable types before passing
    to tasks, or register custom JSON encoders. Better: pass primitives
    (strings, ints, floats) or store complex objects in DB and pass IDs.
    """
    help = 'Q39 Solution: JSON-safe type handling'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q39 SOLUTION: JSON-safe task parameters')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Solution 1: Convert to primitives before passing
        @app.task
        def safe_process_amount_v1(amount_float):
            """Task accepts float instead of Decimal."""
            amount = Decimal(str(amount_float))  # Reconstructed with full precision
            self.stdout.write(f'  Amount: {amount} (reconstructed from {amount_float})')
            return float(amount)

        # Solution 2: Pass object ID, fetch in task
        @app.task
        def safe_process_amount_v2(order_id):
            """Task accepts order_id, fetches Decimal from DB."""
            order = Order.objects.get(pk=order_id)
            self.stdout.write(f'  Amount (from DB): {order.amount}')
            return float(order.amount)

        # Solution 3: Custom JSON encoder (global)
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f'Type {type(obj)} not serializable')

        order = Order.objects.create(
            order_number='Q39-SOL-ORDER',
            customer_email='q39sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nSolution 1: Convert Decimal to float')
        safe_process_amount_v1(float(order.amount))

        self.stdout.write('\nSolution 2: Pass ID, fetch from DB')
        safe_process_amount_v2(order.pk)

        self.stdout.write('\nSolution 3: Custom JSON encoder')
        data = {'amount': order.amount}
        encoded = json.dumps(data, default=decimal_default)
        self.stdout.write(f'  Encoded: {encoded}')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Convert Decimal/datetime to primitives before tasks')
        self.stdout.write('  - Or pass object IDs and fetch in task')
        self.stdout.write('  - Register custom JSON encoders for special types')
        self.stdout.write('  - Test task serialization early in development')
