from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q59 PROBLEM: Large SQS messages (approaching 256KB limit) cause
    failures. Sending DB objects or file content directly in messages
    creates bloated payloads and hits the SQS size limit.
    """
    help = 'Q59 Problem: SQS message size limit - large payload failures'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q59 PROBLEM: SQS message size limit exceeded')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q59-ORD-{i:03}',
                customer_email=f'q59user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        SQS_MAX_SIZE_BYTES = 256 * 1024  # 256KB

        def build_fat_message():
            """Packs all order data directly into the SQS message."""
            orders = list(Order.objects.values())
            # Simulate large payload: embed full report data
            report_data = 'x' * 200_000  # 200KB of fake data
            return {
                'orders': orders,
                'report': report_data,
                'metadata': {'generated_by': 'q59_demo'},
            }

        import json
        msg = build_fat_message()
        msg_size = len(json.dumps(msg, default=str).encode('utf-8'))

        self.stdout.write(f'Message size: {msg_size:,} bytes ({msg_size / 1024:.1f} KB)')
        self.stdout.write(f'SQS limit: {SQS_MAX_SIZE_BYTES:,} bytes (256 KB)')

        if msg_size > SQS_MAX_SIZE_BYTES:
            self.stdout.write(self.style.ERROR(
                f'\nERROR: Message too large by {msg_size - SQS_MAX_SIZE_BYTES:,} bytes!'
                '\n  SQS.send_message() would raise:'
                '\n  MessageTooLong: Message size exceeded maximum allowed size'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Message fits (just barely)'))

        self.stdout.write('\nCommon causes of fat messages:')
        self.stdout.write('  - Embedding full DB record instead of just the ID')
        self.stdout.write('  - Including binary data or base64 encoded files')
        self.stdout.write('  - Nesting entire API responses in messages')
        self.stdout.write('  - Batch of IDs that grows unbounded')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SQS hard limit: 256KB per message')
        self.stdout.write('  - Send only IDs and event type in messages')
        self.stdout.write('  - Use S3 Extended Client for large payloads')
        self.stdout.write('  - Consumers fetch full data from DB/S3 using the ID')
