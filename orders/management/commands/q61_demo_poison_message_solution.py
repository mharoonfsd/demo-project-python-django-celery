from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q61 SOLUTION: Detect poison messages by checking receive count.
    Route to DLQ after maxReceiveCount retries. SQS DLQ handles this
    automatically when configured. Consumer should also log and alert.
    """
    help = 'Q61 Solution: Poison message detection and DLQ routing'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q61 SOLUTION: Poison message handled gracefully')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q61-SOL-ORDER',
            customer_email='q61sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        messages = [
            {'id': 'msg-1', 'order_id': 1, 'receive_count': 1},
            {'id': 'msg-poison', 'order_id': None, 'malformed': True, 'receive_count': 4},
            {'id': 'msg-3', 'order_id': 3, 'receive_count': 1},
        ]

        dlq = []
        MAX_RECEIVE_COUNT = 3

        def process_with_poison_handling(msg):
            """Consumer checks receive count before processing."""
            # Automatic via SQS DLQ maxReceiveCount, or manual check
            if msg['receive_count'] > MAX_RECEIVE_COUNT:
                dlq.append(msg)
                self.stdout.write(self.style.WARNING(
                    f'  {msg["id"]}: Moved to DLQ (receive_count={msg["receive_count"]})'
                ))
                return 'sent_to_dlq'

            if msg.get('malformed'):
                raise ValueError(f'Malformed message {msg["id"]}')

            return f'processed order {msg["order_id"]}'

        self.stdout.write('Consumer processing queue (with poison message handling):')
        for msg in messages:
            try:
                result = process_with_poison_handling(msg)
                if result != 'sent_to_dlq':
                    self.stdout.write(self.style.SUCCESS(f'  {msg["id"]}: {result}'))
                # Continue processing! No blocking.
            except ValueError as e:
                self.stdout.write(f'  {msg["id"]}: error (will retry): {e}')

        self.stdout.write(f'\nDLQ contents: {len(dlq)} message(s)')
        for item in dlq:
            self.stdout.write(f'  - {item["id"]}: malformed={item.get("malformed", False)}')

        self.stdout.write('\nSQS automatic DLQ configuration:')
        self.stdout.write('  Redrive policy: maxReceiveCount=3')
        self.stdout.write('  After 3 failed receives -> auto-moved to DLQ')
        self.stdout.write('  Other messages continue processing unblocked')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Configure maxReceiveCount on SQS queue (3-5 typical)')
        self.stdout.write('  - SQS auto-moves messages to DLQ after maxReceiveCount')
        self.stdout.write('  - Log full message + error context when sending to DLQ')
        self.stdout.write('  - Alert on DLQ depth > 0 via CloudWatch alarm')
