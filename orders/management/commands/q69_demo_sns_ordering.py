from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q69 PROBLEM: SNS message ordering within topics is not guaranteed.
    For standard SNS topics, subscribers may receive messages in different
    order than published. Downstream systems that assume ordering break.
    """
    help = 'Q69 Problem: SNS standard topic - no ordering guarantee'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q69 PROBLEM: SNS standard topic - out-of-order delivery')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q69-ORDER',
            customer_email='q69@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        published = [
            {'seq': 1, 'status': 'pending', 'order_id': order.pk},
            {'seq': 2, 'status': 'confirmed', 'order_id': order.pk},
            {'seq': 3, 'status': 'shipped', 'order_id': order.pk},
        ]

        # Standard SNS: messages may arrive out-of-order at subscriber
        received_subscriber_a = [
            {'seq': 3, 'status': 'shipped'},
            {'seq': 1, 'status': 'pending'},
            {'seq': 2, 'status': 'confirmed'},
        ]

        self.stdout.write('Published to SNS (in order):')
        for msg in published:
            self.stdout.write(f'  seq={msg["seq"]} status={msg["status"]}')

        self.stdout.write('\nReceived at Subscriber A (standard topic - out of order):')
        order_status = None
        for msg in received_subscriber_a:
            self.stdout.write(f'  seq={msg["seq"]} status={msg["status"]}')
            if msg['status'] == 'shipped' and order_status is None:
                order_status = 'shipped'
                self.stdout.write(self.style.ERROR(
                    '    BUG: Marked as shipped before confirmed!'
                ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Order state machine corrupted\n'
            '  - Status jumped to "shipped" before "confirmed"\n'
            '  - Standard SNS: fire-and-forget, no ordering\n'
            '  - Multiple parallel deliveries to different subscribers\n'
            '  - No sequence guarantee even on same topic'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SNS standard topics: no ordering guarantee')
        self.stdout.write('  - SNS FIFO topics: ordered per MessageGroupId')
        self.stdout.write('  - Include sequence number and apply last-write-wins')
        self.stdout.write('  - Consider event sourcing: store all events, rebuild state')
