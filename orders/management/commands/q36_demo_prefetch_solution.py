from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q36 SOLUTION: Set CELERY_WORKER_PREFETCH_MULTIPLIER to 1 for large tasks,
    or use dynamic prefetch based on task size. For small fast tasks, higher
    prefetch (4-10) is fine. Monitor memory and tune accordingly.
    """
    help = 'Q36 Solution: Tune prefetch_multiplier for workload'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q36 SOLUTION: Optimal prefetch configuration')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def efficient_task(order_id):
            """Task with optimized prefetch."""
            order = Order.objects.get(pk=order_id)
            return order.order_number

        order = Order.objects.create(
            order_number='Q36-SOL-ORDER',
            customer_email='q36sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nOptimal prefetch configuration:')
        self.stdout.write('')
        self.stdout.write('For SMALL, FAST tasks (< 1s):')
        self.stdout.write('  CELERY_WORKER_PREFETCH_MULTIPLIER = 4 (default)')
        self.stdout.write('  -> Pull 4 tasks per worker for efficiency')
        self.stdout.write('')
        self.stdout.write('For LARGE, SLOW tasks (> 10s):')
        self.stdout.write('  CELERY_WORKER_PREFETCH_MULTIPLIER = 1')
        self.stdout.write('  -> Pull only 1 task; avoid memory hoarding')
        self.stdout.write('')
        self.stdout.write('Alternative: Use -O fair to disable prefetch')
        self.stdout.write('  celery -A demo_project worker -O fair')
        self.stdout.write('  -> Dynamic load balancing, no prefetch')

        result = efficient_task(order.pk)
        self.stdout.write(f'\nTask result: {result}')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Monitor memory per task type')
        self.stdout.write('  - Set prefetch_multiplier = 1 for large tasks')
        self.stdout.write('  - Use -O fair for balanced load')
        self.stdout.write('  - Profile memory under production load')
