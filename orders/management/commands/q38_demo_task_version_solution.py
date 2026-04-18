from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q38 SOLUTION: Use versioned task names and handle multiple versions
    simultaneously. Accept optional parameters with defaults. Or use a
    gradual rollout: keep old task code for N hours, then remove.
    """
    help = 'Q38 Solution: Versioned tasks with backward compatibility'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q38 SOLUTION: Versioned task handling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Strategy 1: Optional parameters with defaults
        @app.task(name='process_order')
        def process_order_safe(order_id, user_id=None):
            """
            Backward compatible: user_id is optional.
            Old tasks (without user_id) still work.
            New tasks pass user_id.
            """
            if user_id is None:
                self.stdout.write(f'  Processing order {order_id} (legacy, no user)')
            else:
                self.stdout.write(f'  Processing order {order_id} by user {user_id}')
            return 'success'

        # Strategy 2: Version-specific task names
        @app.task(name='process_order_v1')
        def process_order_v1(order_id):
            """Old version kept for backward compatibility."""
            self.stdout.write(f'  [V1] Processing order {order_id}')
            return 'done'

        @app.task(name='process_order_v2')
        def process_order_v2(order_id, user_id):
            """New version with additional parameter."""
            self.stdout.write(f'  [V2] Processing order {order_id} by user {user_id}')
            return 'done'

        order = Order.objects.create(
            order_number='Q38-SOL-ORDER',
            customer_email='q38sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nStrategy 1: Optional parameters')
        self.stdout.write('Old task (no user_id):')
        process_order_safe(order.pk)
        self.stdout.write('New task (with user_id):')
        process_order_safe(order.pk, user_id=42)

        self.stdout.write('\nStrategy 2: Versioned task names')
        self.stdout.write('Old worker runs V1 tasks:')
        process_order_v1(order.pk)
        self.stdout.write('New worker runs V2 tasks:')
        process_order_v2(order.pk, user_id=42)

        self.stdout.write('\nRollout timeline:')
        self.stdout.write('  1. Deploy code with both V1 and V2 tasks')
        self.stdout.write('  2. New tasks use V2, old tasks drain from queue')
        self.stdout.write('  3. After 24h, remove V1 code')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use optional parameters with sensible defaults')
        self.stdout.write('  - Or use versioned task names (task_v1, task_v2)')
        self.stdout.write('  - Never change required parameters')
        self.stdout.write('  - Plan for graceful rollout window')
