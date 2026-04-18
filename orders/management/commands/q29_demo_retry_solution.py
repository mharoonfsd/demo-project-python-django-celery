from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q29 SOLUTION: Use custom retry logic with bounded exponential backoff,
    max_retries limits, and send alerts on final failure. For time-critical
    operations, use shorter backoff windows and prioritize alerting.
    """
    help = 'Q29 Solution: Bounded retry with alerting'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q29 SOLUTION: Smart retry strategy')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(bind=True, max_retries=3)
        def smart_retry_task(self_task, order_id):
            """
            Smart retry:
            1. Limited retries (max 3)
            2. Bounded backoff (max 10s)
            3. Alert on failure
            """
            try:
                print(f'  Attempt {self_task.request.retries + 1}/4')
                # Simulate: might succeed after 2 failures
                if self_task.request.retries < 2:
                    raise Exception('Transient failure')
                return 'success'

            except Exception as exc:
                if self_task.request.retries >= self_task.max_retries:
                    print('  -> Max retries exhausted. ALERT admin!')
                    return 'failed_permanently'

                # Bounded backoff: min 1s, max 10s
                countdown = min(10, 2 ** self_task.request.retries)
                print(f'  -> Retry in {countdown}s')
                return 'retrying'

        order = Order.objects.create(
            order_number='Q29-SOL-ORDER',
            customer_email='q29sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask with smart retry:')
        result = smart_retry_task(order.pk)
        self.stdout.write(self.style.SUCCESS(f'Result: {result}'))

        self.stdout.write('\nRetry benefits:')
        self.stdout.write('  - Max retries prevents infinite loops')
        self.stdout.write('  - Bounded backoff limits delay')
        self.stdout.write('  - Alert on permanent failure')
        self.stdout.write('  - Log all attempts for debugging')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set max_retries to reasonable value (3-5)')
        self.stdout.write('  - Use min() to cap exponential backoff')
        self.stdout.write('  - Alert on final failure')
        self.stdout.write('  - Log retry attempts and reasons')
