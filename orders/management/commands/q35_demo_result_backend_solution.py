from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q35 SOLUTION: Always configure a result backend. Use Redis or PostgreSQL
    as the backend. Store results in the DB for synchronous retrieval.
    Alternatively, use a callback/notification pattern instead of polling.
    """
    help = 'Q35 Solution: Configure result backend for task result storage'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q35 SOLUTION: Result backend configuration')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def compute_total_safe(order_id):
            """Task with result backend configured."""
            order = Order.objects.get(pk=order_id)
            total = order.amount + order.price
            self.stdout.write(f'  Computed total: {total}')
            return float(total)

        order = Order.objects.create(
            order_number='Q35-SOL-ORDER',
            customer_email='q35sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('50.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nWith result backend configured:')
        self.stdout.write('  CELERY_RESULT_BACKEND = "redis://localhost:6379"')
        self.stdout.write('  OR')
        self.stdout.write('  CELERY_RESULT_BACKEND = "db+postgresql://..."')
        self.stdout.write('')

        self.stdout.write('Calling compute_total_safe.delay()...')
        task = compute_total_safe.delay(order.pk)
        self.stdout.write(f'  Task ID: {task.id}')

        self.stdout.write('\nWaiting for result (with timeout):')
        try:
            result = task.get(timeout=10)
            self.stdout.write(self.style.SUCCESS(f'  Result: {result}'))
        except Exception as e:
            self.stdout.write(f'  Exception: {e}')

        self.stdout.write('\nAlternative: Use callbacks instead of polling')
        self.stdout.write('  compute_total_safe.apply_async(..., link=on_success, link_error=on_error)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always configure CELERY_RESULT_BACKEND')
        self.stdout.write('  - Use Redis or PostgreSQL for result storage')
        self.stdout.write('  - Set reasonable result expiry times')
        self.stdout.write('  - Prefer callbacks over blocking .get() calls')
