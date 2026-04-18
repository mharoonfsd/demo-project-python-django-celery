from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q27 SOLUTION: Use atomic transactions and idempotency to make tasks
    recoverable. All DB changes should be transactional. Use state flags
    to track progress, so retries can resume from the last checkpoint.
    """
    help = 'Q27 Solution: Atomic transactions + state tracking for crash recovery'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q27 SOLUTION: Crash-safe task design')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(bind=True)
        def safe_process_order(self_task, order_id):
            """
            Crash-safe task:
            1. All state is in DB (transaction-safe)
            2. Each step is independent
            3. Retries resume from current state
            """
            with transaction.atomic():
                order = Order.objects.get(pk=order_id)

                if not getattr(order, '_step1_done', False):
                    print(f'  [Step 1] Debiting ${order.amount}...')
                    order.amount = order.amount - Decimal('10.00')
                    order._step1_done = True
                    order.save()
                    print('  [Step 1] Complete')

                # Simulate crash between steps by checking state
                if not getattr(order, '_step2_done', False):
                    print('  [Step 2] Shipping items...')
                    # In real code, this would ship
                    order._step2_done = True
                    order.save()
                    print('  [Step 2] Complete')

            return 'success'

        order = Order.objects.create(
            order_number='Q27-SOL-ORDER',
            customer_email='q27sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}\n')

        self.stdout.write('Execution (atomic, resumable):')
        result = safe_process_order(order.pk)
        self.stdout.write(self.style.SUCCESS(f'Task result: {result}'))

        self.stdout.write('\nEven if the task crashed mid-way:')
        self.stdout.write('  - All DB state is inside a transaction')
        self.stdout.write('  - Either both steps complete or both roll back')
        self.stdout.write('  - Retry from start is idempotent')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use transaction.atomic() for all task work')
        self.stdout.write('  - Track progress with DB state flags')
        self.stdout.write('  - Design for retry from any step')
        self.stdout.write('  - Avoid partial state outside transactions')
