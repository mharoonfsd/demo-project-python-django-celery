from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q35 PROBLEM: If the result backend is disabled or not configured, Celery
    does not store task results. Callers waiting for results via task.get()
    will hang or timeout. This is especially problematic for synchronous
    operations expecting a return value.
    """
    help = 'Q35 Problem: Disabled result backend loses task results'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q35 PROBLEM: Result backend disabled causes missing results')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def compute_total(order_id):
            """Task that returns a computed value."""
            order = Order.objects.get(pk=order_id)
            total = order.amount + order.price
            self.stdout.write(f'  Computed total: {total}')
            return float(total)

        order = Order.objects.create(
            order_number='Q35-ORDER',
            customer_email='q35@example.com',
            amount=Decimal('100.00'),
            price=Decimal('50.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nWith result backend disabled:')
        self.stdout.write('  (CELERY_RESULT_BACKEND not configured)')
        self.stdout.write('')

        self.stdout.write('Calling compute_total.delay() and waiting for result...')
        task = compute_total.delay(order.pk)
        self.stdout.write(f'  Task ID: {task.id}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Trying to get result:\n'
            '  task.get(timeout=5) -> raises NotImplementedError or times out\n'
            '  Result not stored anywhere\n'
            '  Caller hangs or gets exception'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Synchronous code expecting results hangs forever')
        self.stdout.write('  - No way to retrieve task outcome')
        self.stdout.write('  - Difficult to debug (looks like task never completed)')
