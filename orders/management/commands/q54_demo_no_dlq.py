from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q54 PROBLEM: Without a Dead Letter Queue (DLQ), messages that fail
    processing are retried forever or silently dropped. You have no way
    to inspect, alert on, or reprocess failed messages.
    """
    help = 'Q54 Problem: No Dead Letter Queue - failed messages lost'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q54 PROBLEM: No DLQ - failed messages disappear')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q54-ORDER',
            customer_email='q54@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        def process_without_dlq(message, attempt=1):
            """Consumer with no DLQ. Retries and eventually drops."""
            try:
                if message.get('corrupted'):
                    raise ValueError(f'Invalid message format: missing required fields')
                return 'processed'
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  Attempt {attempt} FAILED: {e}'
                ))
                if attempt >= 3:
                    self.stdout.write(self.style.ERROR(
                        '  Max retries reached. Message DROPPED - data lost forever!'
                    ))
                    return 'dropped'
                return process_without_dlq(message, attempt + 1)

        self.stdout.write('Processing valid message:')
        result = process_without_dlq({'order_id': order.pk})
        self.stdout.write(f'  Result: {result}')

        self.stdout.write('\nProcessing corrupted message (no DLQ):')
        result = process_without_dlq({'order_id': order.pk, 'corrupted': True})
        self.stdout.write(f'  Result: {result}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No visibility into failures\n'
            '  - Failed message silently dropped after 3 retries\n'
            '  - No alert triggered\n'
            '  - No way to inspect what failed\n'
            '  - No way to reprocess after fixing the bug'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always configure a DLQ on every SQS queue')
        self.stdout.write('  - Set maxReceiveCount (e.g., 3-5 retries before DLQ)')
        self.stdout.write('  - Alert on DLQ depth > 0')
        self.stdout.write('  - Regularly review and replay DLQ messages')
