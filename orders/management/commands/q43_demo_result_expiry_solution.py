from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q43 SOLUTION: Set appropriate CELERY_RESULT_EXPIRES based on task type.
    For short tasks (< 5 min), 1 hour expiry is fine. For long tasks (hours),
    use 24 hours or store results in DB with custom logic.
    """
    help = 'Q43 Solution: Appropriate result TTL configuration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q43 SOLUTION: Tuned result expiry times')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q43-SOL-ORDER',
            customer_email='q43sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nResult expiry recommendations:')
        self.stdout.write('  Short tasks (< 5 min):')
        self.stdout.write('    CELERY_RESULT_EXPIRES = 3600  # 1 hour')
        self.stdout.write('')
        self.stdout.write('  Medium tasks (5 min - 1 hour):')
        self.stdout.write('    CELERY_RESULT_EXPIRES = 86400  # 24 hours')
        self.stdout.write('')
        self.stdout.write('  Long tasks (> 1 hour):')
        self.stdout.write('    Store results in DB with custom model')
        self.stdout.write('    or use callbacks instead of polling')
        self.stdout.write('')
        self.stdout.write('  Critical operations:')
        self.stdout.write('    CELERY_RESULT_EXPIRES = 604800  # 7 days')

        self.stdout.write('\nAlternative: Store results in DB')
        self.stdout.write('  - Create TaskResult model')
        self.stdout.write('  - Task stores result in DB on completion')
        self.stdout.write('  - Client queries DB, not broker')
        self.stdout.write('  - Results never expire (or by business rules)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Match CELERY_RESULT_EXPIRES to task SLA')
        self.stdout.write('  - Use longer TTL for batch/long-running tasks')
        self.stdout.write('  - Consider DB storage for critical results')
        self.stdout.write('  - Monitor result cache hit rate')
