from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q64 PROBLEM: SQS FIFO queue deduplication not configured. Sending the
    same message twice within the 5-minute deduplication window results in
    duplicate processing if MessageDeduplicationId is missing or reused.
    """
    help = 'Q64 Problem: FIFO queue missing deduplication ID'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q64 PROBLEM: FIFO queue missing deduplication')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q64-ORDER',
            customer_email='q64@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        processed_orders = []

        def send_without_dedup_id(event, queue_state):
            """Sends to FIFO queue without MessageDeduplicationId."""
            # No dedup ID = each send is treated as a new unique message
            queue_state.append(event.copy())
            self.stdout.write(f'  Sent: {event["event_type"]} for order {event["order_id"]}')

        def process_fifo_queue(queue_state):
            for msg in queue_state:
                processed_orders.append(msg['order_id'])
                self.stdout.write(f'  Processed: order={msg["order_id"]}')

        queue_state = []

        self.stdout.write('Retry scenario (producer retries on network timeout):')
        event = {'event_type': 'payment_captured', 'order_id': order.pk}

        self.stdout.write('  First send (original):')
        send_without_dedup_id(event, queue_state)

        self.stdout.write('  Producer got timeout, retrying...')
        send_without_dedup_id(event, queue_state)  # retry = duplicate!

        self.stdout.write(f'\n  Queue now has {len(queue_state)} messages')
        self.stdout.write('\nProcessing queue:')
        process_fifo_queue(queue_state)

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Order {order.pk} processed {len(processed_orders)} times!'
            '\n  - FIFO guarantees ordering but NOT deduplication by default'
            '\n  - Must use MessageDeduplicationId for exactly-once sending'
            '\n  - Or enable ContentBasedDeduplication on the queue'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - FIFO queue: must provide MessageDeduplicationId')
        self.stdout.write('  - 5-minute deduplication window - same ID = dropped duplicate')
        self.stdout.write('  - Use hash of message content as dedup ID for idempotency')
        self.stdout.write('  - Enable ContentBasedDeduplication for auto-hashing')
