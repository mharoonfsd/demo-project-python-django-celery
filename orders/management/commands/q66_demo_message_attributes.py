from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q66 PROBLEM: SQS message attributes not used for routing or filtering.
    Consumers parse the full message body to decide whether to process it,
    wasting CPU, memory, and deserialization cost on irrelevant messages.
    """
    help = 'Q66 Problem: Missing message attributes - inefficient filtering'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q66 PROBLEM: No message attributes - parse body to filter')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q66-ORDER',
            customer_email='q66@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        import json

        # Messages without attributes - body must be fully parsed to filter
        messages = [
            {'body': json.dumps({'event': 'order_created', 'region': 'us-east', 'order_id': 1, 'items': ['a'] * 100})},
            {'body': json.dumps({'event': 'inventory_updated', 'region': 'us-west', 'product_id': 5, 'items': ['b'] * 100})},
            {'body': json.dumps({'event': 'order_created', 'region': 'eu-west', 'order_id': 2, 'items': ['c'] * 100})},
            {'body': json.dumps({'event': 'payment_captured', 'region': 'us-east', 'order_id': 1, 'items': ['d'] * 100})},
        ]

        target_event = 'order_created'
        target_region = 'us-east'

        bytes_parsed = 0
        relevant = 0

        self.stdout.write(f'Filtering for event={target_event}, region={target_region}:')
        for i, msg in enumerate(messages):
            bytes_parsed += len(msg['body'].encode())
            body = json.loads(msg['body'])  # Must deserialize full body!
            if body['event'] == target_event and body['region'] == target_region:
                relevant += 1
                self.stdout.write(f'  msg[{i}]: RELEVANT')
            else:
                self.stdout.write(
                    f'  msg[{i}]: irrelevant (wasted {len(msg["body"])} bytes of parsing)'
                )

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Parsed {bytes_parsed:,} bytes to find {relevant} relevant messages'
            f'\n  Efficiency: {relevant}/{len(messages)} = {relevant/len(messages)*100:.0f}%'
            '\n  Message body deserialization costs CPU on EVERY message'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SQS message attributes are outside the body (free to check)')
        self.stdout.write('  - Use attributes for event_type, region, priority, version')
        self.stdout.write('  - SNS filter policy uses attributes (not body) by default')
        self.stdout.write('  - Check attributes BEFORE deserializing body')
