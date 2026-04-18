from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q50 SOLUTION: Enable Redis persistence (AOF) and use RabbitMQ for
    critical workloads. Implement task DB model as backup store.
    Use queue replication or Celery Sentinel.
    """
    help = 'Q50 Solution: Durable broker configuration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q50 SOLUTION: Persistent broker')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q50-SOL-ORDER',
            customer_email='q50sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Strategy 1: Redis persistence (AOF)')
        self.stdout.write('  appendonly yes')
        self.stdout.write('  appendfsync everysec')
        self.stdout.write('  -> Tasks written to disk')
        self.stdout.write('  -> Recovered on restart')
        self.stdout.write('')

        self.stdout.write('Strategy 2: RabbitMQ (durable by default)')
        self.stdout.write('  CELERY_BROKER_URL = amqp://guest:guest@localhost//')
        self.stdout.write('  - Queues are durable (persisted)')
        self.stdout.write('  - Messages persisted if marked durable')
        self.stdout.write('  - Built-in HA with clustering')
        self.stdout.write('')

        self.stdout.write('Strategy 3: Task DB backup')
        self.stdout.write('  - Create TaskRecord model')
        self.stdout.write('  - Save task data to DB on creation')
        self.stdout.write('  - If queue lost, replay from DB')
        self.stdout.write('  - Audit trail for compliance')
        self.stdout.write('')

        self.stdout.write('Strategy 4: Celery Sentinel')
        self.stdout.write('  - Redis Sentinel for HA')
        self.stdout.write('  - Auto-failover to replica')
        self.stdout.write('  - No single point of failure')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Enable Redis AOF for persistence')
        self.stdout.write('  - Use RabbitMQ for critical systems')
        self.stdout.write('  - Implement task DB backup')
        self.stdout.write('  - Use Sentinel for high availability')
