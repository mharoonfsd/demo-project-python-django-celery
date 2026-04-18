from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q90 PROBLEM: Pipeline produces thousands of tiny files (one file per order).
    Each file requires a separate open/close/seek. At scale, the overhead of
    managing many small files dominates actual processing time.
    """
    help = 'Q90 Problem: Many tiny files - open/close overhead dominates'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q90 PROBLEM: Many tiny files - filesystem overhead dominates')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q90-ORD-{i:03}',
                customer_email=f'q90user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import json
        import os
        import tempfile
        import time

        orders = list(Order.objects.values('id', 'order_number', 'amount'))
        tmp_dir = tempfile.mkdtemp()

        # Bad: one file per order
        start = time.monotonic()
        file_paths = []
        for order in orders:
            path = os.path.join(tmp_dir, f'order_{order["id"]}.json')
            with open(path, 'w') as f:
                json.dump({'id': order['id'], 'amount': str(order['amount'])}, f)
            file_paths.append(path)
        write_time_many = time.monotonic() - start

        # Measure read time (many files)
        start = time.monotonic()
        results = []
        for path in file_paths:
            with open(path) as f:
                results.append(json.load(f))
        read_time_many = time.monotonic() - start

        self.stdout.write(f'Many small files ({len(file_paths)} files, 1 order each):')
        self.stdout.write(f'  Write time: {write_time_many*1000:.2f} ms')
        self.stdout.write(f'  Read time:  {read_time_many*1000:.2f} ms')
        self.stdout.write(f'  File operations: {len(file_paths)*2} (open+close per file)')

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: At scale (1M orders = 1M files)'
            f'\n  - 1M open() calls + 1M close() calls = 2M syscalls'
            f'\n  - S3: 1M PUT requests at $0.005/1000 = $5.00 in PUT costs alone'
            f'\n  - S3 LIST limited to 1000 keys per call (1000 API calls to list)'
            f'\n  - Athena/Glue: small file problem -> slow query planning'
            f'\n  - File count often more expensive than file size'
        ))

        # Cleanup
        for path in file_paths:
            os.remove(path)
        os.rmdir(tmp_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Batch writes into fewer, larger files')
        self.stdout.write('  - Target 128MB-1GB file size for analytics workloads')
        self.stdout.write('  - S3: fewer large files -> fewer API calls, cheaper, faster')
        self.stdout.write('  - Partition by date/region, not by row')
