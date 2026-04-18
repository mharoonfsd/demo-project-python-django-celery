from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q46 SOLUTION: Restart worker processes periodically. Use
    CELERYD_MAX_TASKS_PER_CHILD to force worker restart after N tasks.
    Monitor memory and set limits.
    """
    help = 'Q46 Solution: Periodic worker restart to prevent leaks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q46 SOLUTION: Worker lifecycle management')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q46-SOL-ORDER',
            customer_email='q46sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Strategy 1: Max tasks per child process')
        self.stdout.write('  CELERYD_MAX_TASKS_PER_CHILD = 1000')
        self.stdout.write('  -> Worker restarts after 1000 tasks')
        self.stdout.write('  -> Fresh memory each cycle')
        self.stdout.write('')

        self.stdout.write('Strategy 2: Memory limits')
        self.stdout.write('  CELERYD_MAX_MEMORY_PER_CHILD = 500000  # 500 MB')
        self.stdout.write('  -> Child process killed if > 500 MB')
        self.stdout.write('')

        self.stdout.write('Strategy 3: Time-based restart')
        self.stdout.write('  Supervisor: respawn worker every 8 hours')
        self.stdout.write('')

        self.stdout.write('Strategy 4: Monitor and alert')
        self.stdout.write('  - Track worker memory usage')
        self.stdout.write('  - Alert if > threshold')
        self.stdout.write('  - Manually restart if needed')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set CELERYD_MAX_TASKS_PER_CHILD')
        self.stdout.write('  - Set CELERYD_MAX_MEMORY_PER_CHILD')
        self.stdout.write('  - Monitor with prometheus/grafana')
        self.stdout.write('  - Profile for memory leaks')
