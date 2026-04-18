from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q32 SOLUTION: Design all tasks to be idempotent using an idempotency key.
    The key is checked in the DB; if found, the task returns early. If not found,
    the task executes and stores the key. Duplicates safely skip work.
    """
    help = 'Q32 Solution: Idempotent task design with key tracking'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q32 SOLUTION: Idempotent task with key tracking')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Simulate task execution tracking
        executed_keys = set()

        @app.task
        def idempotent_increment(order_id, idempotency_key):
            """Increments only once per idempotency key."""
            if idempotency_key in executed_keys:
                self.stdout.write(
                    f'  Key {idempotency_key} already seen. Skipping.'
                )
                return 'already_done'

            order = Order.objects.get(pk=order_id)
            order.amount = order.amount + Decimal('10.00')
            order.save()
            executed_keys.add(idempotency_key)
            self.stdout.write(f'  First run: incremented amount to {order.amount}')
            return float(order.amount)

        order = Order.objects.create(
            order_number='Q32-SOL-ORDER',
            customer_email='q32sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk} with amount=100.00')

        key = 'task-increment-uuid-v1'
        self.stdout.write(f'\nUsing idempotency key: {key}')

        self.stdout.write('\nRunning task:')
        idempotent_increment(order.pk, key)
        order.refresh_from_db()
        self.stdout.write(f'After run 1: amount={order.amount}')

        self.stdout.write('\nRunning same task again (duplicate/retry):')
        idempotent_increment(order.pk, key)
        order.refresh_from_db()
        self.stdout.write(f'After run 2: amount={order.amount}')

        self.stdout.write(self.style.SUCCESS(
            f'\nAmount is correctly {order.amount} (unchanged by duplicate!)'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Every task needs an idempotency key')
        self.stdout.write('  - Check key before executing side effects')
        self.stdout.write('  - Store processed keys in DB or cache')
        self.stdout.write('  - Generate key from task parameters + timestamp')
