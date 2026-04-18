from decimal import Decimal
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q59 SOLUTION: Send only IDs and event type in SQS messages. Consumer
    fetches data from DB/S3 using the ID. For truly large payloads, use
    the S3 Extended Client pattern (store in S3, send S3 key in SQS).
    """
    help = 'Q59 Solution: Thin messages - IDs only, fetch data in consumer'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q59 SOLUTION: Thin SQS messages with S3 offload')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q59-SOL-ORDER',
            customer_email='q59sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        SQS_MAX_SIZE_BYTES = 256 * 1024

        # Strategy 1: Thin message - ID only
        thin_message = {
            'event': 'order_created',
            'order_id': order.pk,
            'timestamp': '2024-01-01T00:00:00Z',
        }
        thin_size = len(json.dumps(thin_message).encode('utf-8'))
        self.stdout.write(f'Strategy 1: Thin message (ID only)')
        self.stdout.write(f'  Message: {thin_message}')
        self.stdout.write(self.style.SUCCESS(
            f'  Size: {thin_size} bytes (vs 200,000+ bytes fat message)'
        ))

        # Strategy 2: S3 Extended Client pattern for truly large payloads
        self.stdout.write('\nStrategy 2: S3 Extended Client pattern')
        self.stdout.write('  Large payload -> S3 bucket -> S3 key in SQS message')
        s3_pointer_message = {
            'event': 'report_ready',
            's3_bucket': 'my-reports-bucket',
            's3_key': 'reports/2024/01/report-001.json',
        }
        s3_size = len(json.dumps(s3_pointer_message).encode('utf-8'))
        self.stdout.write(f'  Message: {s3_pointer_message}')
        self.stdout.write(self.style.SUCCESS(
            f'  Size: {s3_size} bytes (actual data in S3)'
        ))

        # Consumer pattern
        self.stdout.write('\nConsumer pattern:')
        self.stdout.write('  def process(message):')
        self.stdout.write('      order_id = message["order_id"]')
        self.stdout.write('      order = Order.objects.get(pk=order_id)  # fetch from DB')
        self.stdout.write('      # Now process with full data')

        self.stdout.write('\nSize comparison:')
        self.stdout.write(f'  Fat message:  ~200,000 bytes (fails SQS limit)')
        self.stdout.write(self.style.SUCCESS(
            f'  Thin message: {thin_size} bytes (fits easily)'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SQS messages should contain only IDs and event type')
        self.stdout.write('  - Consumer fetches full data from DB/cache by ID')
        self.stdout.write('  - For large payloads: store in S3, put S3 key in SQS')
        self.stdout.write('  - Thin messages are faster, cheaper, and more reliable')
