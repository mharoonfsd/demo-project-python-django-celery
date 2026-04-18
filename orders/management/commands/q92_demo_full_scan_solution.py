from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q92 SOLUTION: Use watermark-based incremental processing. Track max
    processed id or created_at. Each run only processes new rows since last run.
    O(new data) instead of O(total data).
    """
    help = 'Q92 Solution: Watermark-based incremental pipeline'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q92 SOLUTION: Watermark-based incremental processing')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q92-SOL-{i:03}',
                customer_email=f'q92sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        watermark_store = {'last_processed_id': 0}

        def run_incremental_pipeline():
            last_id = watermark_store['last_processed_id']
            new_orders = list(
                Order.objects.filter(id__gt=last_id)
                .values('id', 'amount', 'created_at')
                .order_by('id')
            )
            if not new_orders:
                return 0, last_id

            for order in new_orders:
                pass  # process order

            new_watermark = new_orders[-1]['id']
            watermark_store['last_processed_id'] = new_watermark
            return len(new_orders), new_watermark

        self.stdout.write('Run 1 (initial, watermark=0):')
        processed, watermark = run_incremental_pipeline()
        self.stdout.write(self.style.SUCCESS(
            f'  Processed: {processed} rows, new watermark: {watermark}'
        ))

        self.stdout.write('Run 2 (no new orders):')
        processed, watermark = run_incremental_pipeline()
        self.stdout.write(self.style.SUCCESS(
            f'  Processed: {processed} rows (nothing new) <- fast!'
        ))

        # Add new orders
        Order.objects.create(
            order_number='Q92-SOL-NEW-1',
            customer_email='q92new1@example.com',
            amount=Decimal('75.00'),
            price=Decimal('75.00'),
        )
        Order.objects.create(
            order_number='Q92-SOL-NEW-2',
            customer_email='q92new2@example.com',
            amount=Decimal('75.00'),
            price=Decimal('75.00'),
        )

        self.stdout.write('Run 3 (2 new orders added):')
        processed, watermark = run_incremental_pipeline()
        self.stdout.write(self.style.SUCCESS(
            f'  Processed: {processed} rows (only new ones), watermark: {watermark}'
        ))

        total_rows = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'  Total rows in DB: {total_rows}, scanned: {processed} (not {total_rows})'
        ))

        self.stdout.write('\nWatermark persistence (production):')
        self.stdout.write('  # Store in DB table')
        self.stdout.write('  PipelineState.objects.update_or_create(')
        self.stdout.write('      pipeline="orders_export",')
        self.stdout.write('      defaults={"last_processed_id": new_watermark}')
        self.stdout.write('  )')
        self.stdout.write('  # Or S3: s3.put_object(Key="watermark.json", Body=json.dumps(...))')

        self.stdout.write('\nWatermark considerations:')
        self.stdout.write('  - Use id (auto-increment) or created_at (with index)')
        self.stdout.write('  - id is safer: no clock skew issues')
        self.stdout.write('  - Use safe_lag: watermark = max_id - 1 (for in-flight rows)')
        self.stdout.write('  - Test: ensure no rows are missed at boundaries')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Track watermark: last processed id or timestamp')
        self.stdout.write('  - Each run: filter(id__gt=last_watermark)')
        self.stdout.write('  - O(new rows) instead of O(total rows)')
        self.stdout.write('  - Persist watermark atomically with processed output')
