from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q60 SOLUTION: Configure SNS subscription filter policies so each
    subscriber only receives relevant messages. Reduces Lambda invocations,
    SQS processing, and overall system load.
    """
    help = 'Q60 Solution: SNS subscription filter policy'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q60 SOLUTION: SNS subscription filter policies')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q60-SOL-ORDER',
            customer_email='q60sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        events = [
            {'event_type': 'order_created', 'order_id': 1},
            {'event_type': 'payment_captured', 'order_id': 1},
            {'event_type': 'order_shipped', 'order_id': 1},
            {'event_type': 'inventory_updated', 'product_id': 5},
        ]

        # Filter policies - each subscriber only gets matching events
        email_filter = {'event_type': ['order_created']}
        shipping_filter = {'event_type': ['payment_captured']}

        def matches_filter(event, filter_policy):
            for attr, allowed_values in filter_policy.items():
                if event.get(attr) not in allowed_values:
                    return False
            return True

        email_invocations = 0
        shipping_invocations = 0
        total_events = len(events)

        self.stdout.write('Events with filter policy applied:')
        for event in events:
            email_receives = matches_filter(event, email_filter)
            shipping_receives = matches_filter(event, shipping_filter)

            status = []
            if email_receives:
                email_invocations += 1
                status.append('email=RECEIVED')
            else:
                status.append('email=filtered')
            if shipping_receives:
                shipping_invocations += 1
                status.append('shipping=RECEIVED')
            else:
                status.append('shipping=filtered')

            self.stdout.write(f'  {event["event_type"]}: {", ".join(status)}')

        self.stdout.write(f'\nEmail service: {email_invocations}/{total_events} events')
        self.stdout.write(f'Shipping service: {shipping_invocations}/{total_events} events')
        self.stdout.write(self.style.SUCCESS(
            f'Total invocations: {email_invocations + shipping_invocations} (vs {total_events * 2} without filter)'
        ))

        self.stdout.write('\nFilter policy configuration (boto3):')
        self.stdout.write('  sns.subscribe(')
        self.stdout.write('      TopicArn=topic_arn,')
        self.stdout.write('      Protocol="sqs",')
        self.stdout.write('      Endpoint=email_queue_arn,')
        self.stdout.write('      Attributes={')
        self.stdout.write('          "FilterPolicy": \'{"event_type": ["order_created"]}\'')
        self.stdout.write('      }')
        self.stdout.write('  )')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set FilterPolicy on each SNS subscription')
        self.stdout.write('  - Filter on message attributes (not body - body filtering costs more)')
        self.stdout.write('  - Each subscriber only processes relevant messages')
        self.stdout.write('  - Reduces Lambda cost, SQS processing, and latency')
