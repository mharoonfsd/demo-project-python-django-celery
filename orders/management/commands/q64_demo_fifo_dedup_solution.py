from decimal import Decimal
import hashlib
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q64 SOLUTION: Always provide MessageDeduplicationId on FIFO queues.
    Generate it deterministically from message content (hash). Within the
    5-minute window, SQS drops messages with duplicate IDs.
    """
    help = 'Q64 Solution: FIFO queue with MessageDeduplicationId'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q64 SOLUTION: FIFO deduplication with deterministic ID')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q64-SOL-ORDER',
            customer_email='q64sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        processed_orders = []
        dedup_store = set()  # SQS maintains this for 5 minutes

        def make_dedup_id(event):
            """Deterministic dedup ID from message content."""
            content = json.dumps(event, sort_keys=True)
            return hashlib.sha256(content.encode()).hexdigest()[:16]

        def send_with_dedup_id(event, queue_state):
            """Sends to FIFO queue with MessageDeduplicationId."""
            dedup_id = make_dedup_id(event)
            if dedup_id in dedup_store:
                self.stdout.write(self.style.WARNING(
                    f'  Duplicate detected (dedup_id={dedup_id}) - message dropped by SQS'
                ))
                return False
            dedup_store.add(dedup_id)
            queue_state.append({**event, '_dedup_id': dedup_id})
            self.stdout.write(self.style.SUCCESS(
                f'  Sent: {event["event_type"]} dedup_id={dedup_id}'
            ))
            return True

        queue_state = []
        event = {'event_type': 'payment_captured', 'order_id': order.pk}

        self.stdout.write('Producer sends with retry:')
        send_with_dedup_id(event, queue_state)
        self.stdout.write('  Producer got timeout, retrying...')
        send_with_dedup_id(event, queue_state)  # duplicate dropped!

        self.stdout.write(f'\nQueue has {len(queue_state)} message(s) (duplicate dropped)')

        self.stdout.write('\nProcessing queue:')
        for msg in queue_state:
            processed_orders.append(msg['order_id'])
            self.stdout.write(self.style.SUCCESS(
                f'  Processed order {msg["order_id"]} exactly once!'
            ))

        self.stdout.write('\nboto3 FIFO send example:')
        self.stdout.write('  sqs.send_message(')
        self.stdout.write('      QueueUrl="https://sqs...queue.fifo",')
        self.stdout.write('      MessageBody=json.dumps(event),')
        self.stdout.write('      MessageGroupId=f"order-{order_id}",')
        self.stdout.write('      MessageDeduplicationId=make_dedup_id(event),')
        self.stdout.write('  )')

        self.stdout.write('\nContentBasedDeduplication (queue setting):')
        self.stdout.write('  AWS auto-hashes message body as dedup ID')
        self.stdout.write('  No need to set MessageDeduplicationId manually')
        self.stdout.write('  Only works if same event always has identical body')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always set MessageDeduplicationId on FIFO queues')
        self.stdout.write('  - Use deterministic hash of event content as dedup ID')
        self.stdout.write('  - Or enable ContentBasedDeduplication on queue')
        self.stdout.write('  - 5-minute window: same ID within window = dropped')
