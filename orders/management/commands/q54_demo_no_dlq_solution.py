from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q54 SOLUTION: Configure a DLQ for every SQS queue. Set maxReceiveCount
    to control retry attempts. Alert on DLQ depth. Build tooling to inspect
    and replay failed messages.
    """
    help = 'Q54 Solution: DLQ configuration and monitoring'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q54 SOLUTION: DLQ configuration and monitoring')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q54-SOL-ORDER',
            customer_email='q54sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        dlq = []  # Simulated DLQ

        def process_with_dlq(message, max_retries=3):
            """Consumer that routes failed messages to DLQ."""
            for attempt in range(1, max_retries + 1):
                try:
                    if message.get('corrupted'):
                        raise ValueError('Invalid message format')
                    self.stdout.write(self.style.SUCCESS(
                        f'  Processed successfully on attempt {attempt}'
                    ))
                    return 'processed'
                except Exception as e:
                    self.stdout.write(f'  Attempt {attempt} failed: {e}')
                    if attempt == max_retries:
                        dlq.append({'message': message, 'error': str(e), 'attempts': attempt})
                        self.stdout.write(self.style.WARNING(
                            f'  Moved to DLQ after {max_retries} retries'
                        ))
                        return 'sent_to_dlq'
            return 'dropped'

        self.stdout.write('Processing valid message:')
        result = process_with_dlq({'order_id': order.pk})
        self.stdout.write(f'  Result: {result}')

        self.stdout.write('\nProcessing corrupted message (with DLQ):')
        result = process_with_dlq({'order_id': order.pk, 'corrupted': True})
        self.stdout.write(f'  Result: {result}')

        self.stdout.write(f'\nDLQ depth: {len(dlq)} messages')
        if dlq:
            self.stdout.write(self.style.WARNING('  ALERT: DLQ depth > 0!'))
            for item in dlq:
                self.stdout.write(f'  - Error: {item["error"]}, Attempts: {item["attempts"]}')

        self.stdout.write('\nAWS CDK/Terraform DLQ configuration:')
        self.stdout.write('  dead_letter_queue = sqs.Queue(self, "MyDLQ")')
        self.stdout.write('  main_queue = sqs.Queue(')
        self.stdout.write('    self, "MainQueue",')
        self.stdout.write('    dead_letter_queue={')
        self.stdout.write('      "queue": dead_letter_queue,')
        self.stdout.write('      "max_receive_count": 3')
        self.stdout.write('    }')
        self.stdout.write('  )')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Attach DLQ to every SQS queue (maxReceiveCount=3-5)')
        self.stdout.write('  - CloudWatch alarm: DLQDepth > 0 -> PagerDuty alert')
        self.stdout.write('  - Build replay tool: read DLQ -> fix bug -> resend to main queue')
        self.stdout.write('  - Include original message + error context in DLQ message')
