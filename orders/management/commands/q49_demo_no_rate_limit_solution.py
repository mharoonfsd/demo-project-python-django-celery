from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q49 SOLUTION: Use Celery rate_limit to throttle tasks. Limit tasks/sec
    by task type. Use throttle decorator or broker rate limits.
    """
    help = 'Q49 Solution: Rate limiting with Celery'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q49 SOLUTION: Rate limiting')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(rate_limit='100/m')  # 100 tasks per minute
        def send_email_throttled(order_id):
            """Task with rate limit: 100/minute."""
            return 'sent'

        @app.task(rate_limit='10/s')  # 10 tasks per second
        def process_payment(order_id):
            """Task with rate limit: 10/second."""
            return 'charged'

        order = Order.objects.create(
            order_number='Q49-SOL-ORDER',
            customer_email='q49sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Strategy 1: Celery task rate_limit')
        self.stdout.write('  @app.task(rate_limit="100/m")')
        self.stdout.write('  @app.task(rate_limit="10/s")')
        self.stdout.write('  @app.task(rate_limit="1000/h")')
        self.stdout.write('')

        self.stdout.write('Strategy 2: Broker-level rate limits')
        self.stdout.write('  CELERY_TASK_ROUTES = {')
        self.stdout.write('      "orders.tasks.send_email": {"rate_limit": "100/m"},')
        self.stdout.write('  }')
        self.stdout.write('')

        self.stdout.write('Strategy 3: Manual queue throttling')
        self.stdout.write('  - Check queue depth before enqueue')
        self.stdout.write('  - Reject if queue > threshold')
        self.stdout.write('  - Return 429 Too Many Requests to client')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set rate_limit on all tasks')
        self.stdout.write('  - Match to SLA and resource capacity')
        self.stdout.write('  - Monitor queue depth and adjust')
        self.stdout.write('  - Use 429 backpressure to clients')
