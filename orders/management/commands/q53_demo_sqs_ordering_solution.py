from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q53 SOLUTION: Use SQS FIFO queues for strict ordering, or design consumers
    to handle out-of-order messages using sequence numbers and idempotency.
    """
    help = 'Q53 Solution: FIFO queues or order-tolerant consumer design'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q53 SOLUTION: Handle ordering in SQS')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q53-SOL-ORDER',
            customer_email='q53sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate out-of-order events arriving
        received_events = [
            {'seq': 3, 'event': 'order_shipped'},
            {'seq': 1, 'event': 'order_created'},
            {'seq': 2, 'event': 'payment_captured'},
        ]

        self.stdout.write('Strategy 1: SQS FIFO Queue (.fifo suffix)')
        self.stdout.write('  - Queue name must end in .fifo')
        self.stdout.write('  - Add MessageGroupId for per-entity ordering')
        self.stdout.write('  - Add MessageDeduplicationId for exactly-once')
        self.stdout.write('  - Tradeoff: 300 TPS limit (3000 with batching)')
        self.stdout.write('')

        self.stdout.write('Strategy 2: Sequence-aware consumer (standard queue)')
        # Buffer and sort by sequence number
        buffer = sorted(received_events, key=lambda e: e['seq'])
        self.stdout.write('  Events buffered and sorted by seq:')
        for e in buffer:
            self.stdout.write(f'    seq={e["seq"]} {e["event"]}')

        self.stdout.write('')
        self.stdout.write('Strategy 3: Idempotent state machine')
        self.stdout.write('  - Each event carries full state (not delta)')
        self.stdout.write('  - Consumer applies "latest wins" by timestamp')
        self.stdout.write('  - Works with any delivery order')

        self.stdout.write('\nFIFO vs Standard comparison:')
        self.stdout.write('  Standard: unlimited TPS, at-least-once, best-effort order')
        self.stdout.write('  FIFO: 300/3000 TPS, exactly-once, strict order')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use FIFO for order-sensitive workflows')
        self.stdout.write('  - Include seq number + timestamp in all messages')
        self.stdout.write('  - Design consumers to be order-tolerant when possible')
        self.stdout.write('  - Group related messages with MessageGroupId')
