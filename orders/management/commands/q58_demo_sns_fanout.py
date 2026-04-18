from decimal import Decimal
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q58 PROBLEM: SNS fanout to multiple SQS queues fails silently when
    subscription configuration is wrong. Missing raw message delivery,
    wrong permissions, or missing subscriptions cause data loss.
    """
    help = 'Q58 Problem: SNS fanout misconfiguration - silent data loss'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q58 PROBLEM: SNS fanout misconfiguration')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q58-ORDER',
            customer_email='q58@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate SNS message (without RawMessageDelivery enabled)
        event = {'order_id': order.pk, 'event': 'order_created'}

        # Without RawMessageDelivery, SNS wraps message in envelope
        sns_envelope = {
            'Type': 'Notification',
            'MessageId': 'abc-123',
            'TopicArn': 'arn:aws:sns:us-east-1:123:orders',
            'Message': json.dumps(event),  # nested JSON string!
            'Timestamp': '2024-01-01T00:00:00.000Z',
        }

        def process_message_wrong(raw_body):
            """Consumer assumes direct JSON, not SNS envelope."""
            data = json.loads(raw_body)
            order_id = data['order_id']   # KeyError! 'order_id' not at top level
            return order_id

        self.stdout.write('Publishing event to SNS topic...')
        self.stdout.write(f'  Event: {event}')

        self.stdout.write('\nConsumer receives SQS message (SNS envelope):')
        raw_body = json.dumps(sns_envelope)
        self.stdout.write(f'  Message body preview: {raw_body[:80]}...')

        self.stdout.write('\nConsumer parsing without envelope handling:')
        try:
            result = process_message_wrong(raw_body)
            self.stdout.write(f'  Result: {result}')
        except KeyError as e:
            self.stdout.write(self.style.ERROR(
                f'  KeyError: {e} - consumer expected flat JSON but got SNS envelope!'
            ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Two root causes\n'
            '  1. RawMessageDelivery=false (default): SNS wraps in envelope\n'
            '     Consumer code breaks expecting direct JSON\n'
            '  2. Wrong IAM policy: SQS queue denies SNS publish permission\n'
            '     Messages silently lost, no error on producer side'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Enable RawMessageDelivery=true on SNS->SQS subscription')
        self.stdout.write('  - Or handle SNS envelope in consumer (parse Message field)')
        self.stdout.write('  - Grant sqs:SendMessage to SNS topic ARN in SQS policy')
        self.stdout.write('  - Test fanout paths end-to-end before deploying')
