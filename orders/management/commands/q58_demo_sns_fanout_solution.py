from decimal import Decimal
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q58 SOLUTION: Enable RawMessageDelivery=true, or handle SNS envelope
    in consumer code. Verify SQS resource policy allows sns:Publish.
    """
    help = 'Q58 Solution: SNS fanout with correct configuration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q58 SOLUTION: SNS fanout - correct handling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q58-SOL-ORDER',
            customer_email='q58sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        event = {'order_id': order.pk, 'event': 'order_created'}

        sns_envelope = {
            'Type': 'Notification',
            'MessageId': 'abc-123',
            'TopicArn': 'arn:aws:sns:us-east-1:123:orders',
            'Message': json.dumps(event),
        }

        def process_message_correct(raw_body):
            """Consumer handles both SNS envelope and raw JSON."""
            data = json.loads(raw_body)
            # Handle SNS envelope wrapping
            if data.get('Type') == 'Notification':
                data = json.loads(data['Message'])
            order_id = data['order_id']
            return order_id

        self.stdout.write('Strategy 1: Handle SNS envelope in consumer')
        raw_body = json.dumps(sns_envelope)
        result = process_message_correct(raw_body)
        self.stdout.write(self.style.SUCCESS(
            f'  Parsed successfully: order_id={result}'
        ))

        self.stdout.write('\nStrategy 2: Enable RawMessageDelivery (recommended)')
        self.stdout.write('  boto3: sns.subscribe(')
        self.stdout.write('      TopicArn=topic_arn,')
        self.stdout.write('      Protocol="sqs",')
        self.stdout.write('      Endpoint=queue_arn,')
        self.stdout.write('      Attributes={"RawMessageDelivery": "true"}')
        self.stdout.write('  )')
        self.stdout.write('  -> Consumer receives direct JSON, no envelope')

        self.stdout.write('\nRequired SQS resource policy:')
        self.stdout.write('  {')
        self.stdout.write('    "Effect": "Allow",')
        self.stdout.write('    "Principal": {"Service": "sns.amazonaws.com"},')
        self.stdout.write('    "Action": "sqs:SendMessage",')
        self.stdout.write('    "Resource": "arn:aws:sqs:...:my-queue",')
        self.stdout.write('    "Condition": {')
        self.stdout.write('      "ArnEquals": {"aws:SourceArn": "arn:aws:sns:...:my-topic"}')
        self.stdout.write('    }')
        self.stdout.write('  }')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Prefer RawMessageDelivery=true for simpler consumers')
        self.stdout.write('  - Alternatively handle SNS envelope in all consumers')
        self.stdout.write('  - Always set correct SQS resource policy for SNS publish')
        self.stdout.write('  - Use AWS CDK/Terraform to manage these policies as code')
