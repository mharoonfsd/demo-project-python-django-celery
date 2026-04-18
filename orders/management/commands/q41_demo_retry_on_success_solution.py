from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q41 SOLUTION: Only retry on specific, recoverable exceptions (e.g.,
    TimeoutError, ConnectionError). Never retry on all Exception. Let
    non-recoverable errors fail permanently.
    """
    help = 'Q41 Solution: Selective retry on specific exceptions'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q41 SOLUTION: Retry only on transient exceptions')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(
            bind=True,
            max_retries=3,
            autoretry_for=(TimeoutError, ConnectionError),  # Only these
            retry_kwargs={'max_retries': 3}
        )
        def safe_retry_task(self_task, order_id):
            """Retry only on transient errors."""
            order = Order.objects.get(pk=order_id)
            print(f'  Processing order (will succeed)')
            # This succeeds on first try, no retry
            return 'done'

        order = Order.objects.create(
            order_number='Q41-SOL-ORDER',
            customer_email='q41sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask with selective retry:')
        result = safe_retry_task(order.pk)
        self.stdout.write(f'  Result: {result} (no unnecessary retries)')

        self.stdout.write('\nExceptions to retry:')
        self.stdout.write('  - TimeoutError (network timeout)')
        self.stdout.write('  - ConnectionError (DB down temporarily)')
        self.stdout.write('  - Celery.TaskPredicate (task rejected)')
        self.stdout.write('')
        self.stdout.write('Exceptions to NOT retry:')
        self.stdout.write('  - ValueError (bad input, won\'t fix on retry)')
        self.stdout.write('  - KeyError (missing key in data)')
        self.stdout.write('  - TypeError (code bug)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use autoretry_for with specific exception types')
        self.stdout.write('  - Never autoretry on all Exception')
        self.stdout.write('  - Log which exception triggered retry')
        self.stdout.write('  - Alert on non-retryable exceptions')
