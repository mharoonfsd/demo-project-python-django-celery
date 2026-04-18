from decimal import Decimal
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q66 SOLUTION: Include routing metadata as SQS message attributes.
    Check attributes before deserializing body. Use SNS filter policies
    on attributes to prevent irrelevant messages from reaching consumers.
    """
    help = 'Q66 Solution: Message attributes for efficient filtering'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q66 SOLUTION: Message attributes for pre-filter routing')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q66-SOL-ORDER',
            customer_email='q66sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Messages with attributes - can filter WITHOUT parsing body
        messages = [
            {
                'attributes': {'event_type': 'order_created', 'region': 'us-east'},
                'body': json.dumps({'order_id': 1, 'items': ['a'] * 100}),
            },
            {
                'attributes': {'event_type': 'inventory_updated', 'region': 'us-west'},
                'body': json.dumps({'product_id': 5, 'items': ['b'] * 100}),
            },
            {
                'attributes': {'event_type': 'order_created', 'region': 'eu-west'},
                'body': json.dumps({'order_id': 2, 'items': ['c'] * 100}),
            },
            {
                'attributes': {'event_type': 'payment_captured', 'region': 'us-east'},
                'body': json.dumps({'order_id': 1, 'items': ['d'] * 100}),
            },
        ]

        target_event = 'order_created'
        target_region = 'us-east'
        bytes_parsed = 0
        relevant = 0

        self.stdout.write(f'Filtering for event={target_event}, region={target_region}:')
        for i, msg in enumerate(messages):
            attrs = msg['attributes']
            if attrs['event_type'] == target_event and attrs['region'] == target_region:
                bytes_parsed += len(msg['body'].encode())
                body = json.loads(msg['body'])  # Only parse when needed
                relevant += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  msg[{i}]: RELEVANT - processing order {body["order_id"]}'
                ))
            else:
                self.stdout.write(
                    f'  msg[{i}]: filtered by attribute (body NOT parsed)'
                )

        total_bytes = sum(len(m['body'].encode()) for m in messages)
        self.stdout.write(self.style.SUCCESS(
            f'\nParsed only {bytes_parsed:,} / {total_bytes:,} bytes'
        ))

        self.stdout.write('\nboto3 send with message attributes:')
        self.stdout.write('  sqs.send_message(')
        self.stdout.write('      QueueUrl=queue_url,')
        self.stdout.write('      MessageBody=json.dumps(event),')
        self.stdout.write('      MessageAttributes={')
        self.stdout.write('          "event_type": {"DataType": "String", "StringValue": "order_created"},')
        self.stdout.write('          "region": {"DataType": "String", "StringValue": "us-east"},')
        self.stdout.write('      }')
        self.stdout.write('  )')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Add event_type, region, priority as message attributes')
        self.stdout.write('  - Filter on attributes BEFORE deserializing body')
        self.stdout.write('  - SNS filter policy also uses attributes (not body)')
        self.stdout.write('  - Reduces CPU and memory for irrelevant messages')
