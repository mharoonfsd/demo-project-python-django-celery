from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q34 PROBLEM: If Redis (the Celery broker) goes down, the task queue
    becomes unavailable. New tasks cannot be enqueued, and workers have
    nothing to do. This causes complete outage until Redis recovers.
    """
    help = 'Q34 Problem: Redis broker down causes queue outage'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q34 PROBLEM: Redis broker failure stops queue')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def send_notification(order_id):
            """Task to send notification."""
            order = Order.objects.get(pk=order_id)
            self.stdout.write(f'  Sending notification to {order.customer_email}')
            return 'sent'

        order = Order.objects.create(
            order_number='Q34-ORDER',
            customer_email='q34@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nScenario: Attempting to queue task while Redis is down')
        self.stdout.write('(Redis typically running on localhost:6379)')
        self.stdout.write('')

        try:
            self.stdout.write('Calling send_notification.delay()...')
            # In production, this would hang or timeout
            send_notification.delay(order.pk)
            self.stdout.write(self.style.ERROR(
                'ERROR: ConnectionRefusedError or timeout\n'
                '  Can\'t connect to Redis broker at localhost:6379'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Exception: {type(e).__name__}: {e}'))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Complete queue outage:\n'
            '  - New tasks cannot be enqueued\n'
            '  - Workers go idle (nothing to process)\n'
            '  - All delayed notifications lost\n'
            '  - System appears down to users'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Single point of failure (Redis)')
        self.stdout.write('  - Tasks lost if not persisted elsewhere')
        self.stdout.write('  - No visibility into outage duration')
