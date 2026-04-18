from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q34 SOLUTION: Use Redis Sentinel for high availability, or switch to
    RabbitMQ with native clustering. Additionally, queue tasks in the DB
    as a fallback. If Redis is down, fall back to polling the DB queue.
    """
    help = 'Q34 Solution: High-availability broker + DB fallback'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q34 SOLUTION: HA broker + DB fallback queue')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Simulate: task queue table in DB as fallback
        queued_tasks = []

        @app.task
        def resilient_send_notification(order_id):
            """Send notification with fallback to DB queue."""
            order = Order.objects.get(pk=order_id)
            self.stdout.write(f'  Sending notification to {order.customer_email}')
            return 'sent'

        def enqueue_with_fallback(order_id):
            """Try Redis first, fallback to DB queue."""
            try:
                self.stdout.write('  [1] Attempting to queue in Redis...')
                resilient_send_notification.delay(order_id)
                self.stdout.write('  [OK] Task queued in Redis')
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'  [FALLBACK] Redis unavailable ({e})'
                ))
                self.stdout.write('  [2] Storing task in DB queue...')
                queued_tasks.append({'order_id': order_id, 'task': 'send_notification'})
                self.stdout.write('  [OK] Task stored in DB for later processing')

        order = Order.objects.create(
            order_number='Q34-SOL-ORDER',
            customer_email='q34sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nScenario: Redis down, but DB fallback available')
        enqueue_with_fallback(order.pk)

        self.stdout.write('\nQueued tasks (DB fallback): {len(queued_tasks)}')
        self.stdout.write('When Redis recovers, retry DB queue.')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use Redis Sentinel for automatic failover')
        self.stdout.write('  - Or switch to RabbitMQ with native HA')
        self.stdout.write('  - Implement DB fallback for non-critical tasks')
        self.stdout.write('  - Monitor broker health and alert on outage')
