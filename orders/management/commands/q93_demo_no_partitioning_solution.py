from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q93 SOLUTION: Partition output by date. Only relevant partitions
    are read for each query. Show partition pruning in action.
    """
    help = 'Q93 Solution: Partition by date for efficient query pruning'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q93 SOLUTION: Partitioned output with pruning')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        from datetime import date, timedelta
        import json
        import os
        import tempfile

        dates = ['2024-01-14', '2024-01-14', '2024-01-15', '2024-01-15',
                 '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16',
                 '2024-01-17', '2024-01-17']
        for i, d in enumerate(dates, 1):
            Order.objects.create(
                order_number=f'Q93-SOL-{i:03}',
                customer_email=f'q93sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        orders = list(Order.objects.values('id', 'amount', 'created_at'))
        records = [
            {'id': o['id'], 'amount': str(o['amount']),
             'date': dates[i % len(dates)]}
            for i, o in enumerate(orders)
        ]

        tmp_dir = tempfile.mkdtemp()

        # Partition by date
        from collections import defaultdict
        partitions = defaultdict(list)
        for record in records:
            partitions[record['date']].append(record)

        self.stdout.write('Writing partitioned output:')
        partition_paths = {}
        for date_val, rows in sorted(partitions.items()):
            year, month, day = date_val.split('-')
            part_dir = os.path.join(tmp_dir, f'year={year}', f'month={month}', f'day={day}')
            os.makedirs(part_dir, exist_ok=True)
            path = os.path.join(part_dir, 'part-0001.json')
            with open(path, 'w') as f:
                json.dump(rows, f)
            partition_paths[date_val] = path
            self.stdout.write(self.style.SUCCESS(
                f'  {path.replace(tmp_dir, "output")} -> {len(rows)} rows'
            ))

        # Partition pruning query
        query_date = '2024-01-15'
        self.stdout.write(f'\nQuery: orders for date={query_date}')
        all_dates = list(partitions.keys())
        scanned_dates = [d for d in all_dates if d == query_date]
        skipped_dates = [d for d in all_dates if d != query_date]

        self.stdout.write(f'  Partitions scanned: {scanned_dates} ({len(partitions[query_date])} rows)')
        self.stdout.write(self.style.SUCCESS(
            f'  Partitions skipped: {skipped_dates} (0 rows read)'
        ))
        total_rows = sum(len(v) for v in partitions.values())
        scanned_rows = len(partitions[query_date])
        self.stdout.write(self.style.SUCCESS(
            f'  Rows scanned: {scanned_rows}/{total_rows} '
            f'({scanned_rows*100//total_rows}% — partition pruning)'
        ))

        self.stdout.write('\nS3 partition layout:')
        self.stdout.write('  s3://bucket/orders/year=2024/month=01/day=14/part-0001.parquet')
        self.stdout.write('  s3://bucket/orders/year=2024/month=01/day=15/part-0001.parquet')
        self.stdout.write('  ...')

        self.stdout.write('\nAthena: registers partitions automatically')
        self.stdout.write('  MSCK REPAIR TABLE orders;  -- discover new partitions')
        self.stdout.write('  -- or use partition projection for dynamic partitioning')

        # Cleanup
        import shutil
        shutil.rmtree(tmp_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Partition by most common query filter (usually date)')
        self.stdout.write('  - Partition pruning: query scans only matching partitions')
        self.stdout.write('  - Athena costs proportional to bytes scanned — partitioning saves $')
        self.stdout.write('  - year=/month=/day= is the standard Hive partition format')
