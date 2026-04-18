from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q90 SOLUTION: Batch records into a single file (or a few partitioned files).
    Use date/region partitioning for manageable file counts.
    Show I/O overhead reduction.
    """
    help = 'Q90 Solution: Batch into fewer large files with partitioning'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q90 SOLUTION: Batch writes reduce file count and overhead')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q90-SOL-{i:03}',
                customer_email=f'q90sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import json
        import os
        import tempfile
        import time

        orders = list(Order.objects.values('id', 'order_number', 'amount', 'created_at'))
        tmp_dir = tempfile.mkdtemp()

        # Good: all orders in ONE file
        start = time.monotonic()
        batch_path = os.path.join(tmp_dir, 'orders_batch.json')
        records = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]
        with open(batch_path, 'w') as f:
            json.dump(records, f)
        write_time_one = time.monotonic() - start

        start = time.monotonic()
        with open(batch_path) as f:
            loaded = json.load(f)
        read_time_one = time.monotonic() - start

        self.stdout.write(f'Single batched file ({len(records)} orders):')
        self.stdout.write(self.style.SUCCESS(f'  Write time: {write_time_one*1000:.2f} ms'))
        self.stdout.write(self.style.SUCCESS(f'  Read time:  {read_time_one*1000:.2f} ms'))
        self.stdout.write(f'  File operations: 2 (1 open + 1 close total)')

        # Partitioned output (by date)
        self.stdout.write('\nPartitioned output pattern:')
        self.stdout.write('  output/')
        self.stdout.write('    year=2024/')
        self.stdout.write('      month=01/')
        self.stdout.write('        part-0001.parquet  (128MB target)')
        self.stdout.write('        part-0002.parquet')
        self.stdout.write('      month=02/')
        self.stdout.write('        part-0001.parquet')
        self.stdout.write('')
        self.stdout.write('  Query: "SELECT * WHERE year=2024 AND month=01"')
        self.stdout.write('  -> Reads ONLY month=01 partition (partition pruning)')
        self.stdout.write('  -> Skips all other months entirely')

        self.stdout.write('\nFile size targets for analytics:')
        self.stdout.write('  - Target: 128MB - 1GB per file')
        self.stdout.write('  - Below 128MB: small file overhead')
        self.stdout.write('  - Above 1GB: hard to parallelize reading')
        self.stdout.write('  - Snappy/gzip compression: 3-5x smaller on disk')

        self.stdout.write('\nS3 costs comparison:')
        self.stdout.write('  1M orders as 1M files: 1M PUT + 1M GET = $10+ per run')
        self.stdout.write('  1M orders as 10 files: 10 PUT + 10 GET = $0.0001 per run')

        # Cleanup
        os.remove(batch_path)
        os.rmdir(tmp_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Batch all records into one file per partition')
        self.stdout.write('  - Target 128MB-1GB per file for analytics workloads')
        self.stdout.write('  - Partition by date/region for efficient query pruning')
        self.stdout.write('  - Fewer files = fewer API calls, lower S3 costs, faster queries')
