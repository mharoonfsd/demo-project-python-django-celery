from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q86 SOLUTION: Use columnar format (Parquet-like) with compression.
    Simulate column pruning and statistics. Demonstrate size and speed
    advantages. In production: use pyarrow or pandas with Parquet on S3.
    """
    help = 'Q86 Solution: Columnar format with compression and column pruning'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q86 SOLUTION: Columnar storage with column pruning')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q86-SOL-{i:03}',
                customer_email=f'q86sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        import json
        import zlib

        orders = list(Order.objects.values(
            'id', 'order_number', 'customer_email', 'amount', 'price'
        ))

        # Simulate columnar storage: one entry per column
        columns = {}
        for order in orders:
            for col, val in order.items():
                columns.setdefault(col, []).append(str(val))

        # Simulate compression per column (similar values compress well)
        csv_size = len(json.dumps([{k: str(v) for k, v in o.items()} for o in orders]).encode())

        columnar_compressed_size = 0
        for col, values in columns.items():
            raw = ','.join(values).encode()
            compressed = zlib.compress(raw, level=6)
            columnar_compressed_size += len(compressed)

        self.stdout.write('Format comparison (simulated, 5 rows):')
        self.stdout.write(f'  Row-oriented CSV (uncompressed): {csv_size:,} bytes')
        self.stdout.write(self.style.SUCCESS(
            f'  Columnar + compressed:           {columnar_compressed_size:,} bytes '
            f'({100 - columnar_compressed_size*100//csv_size}% smaller)'
        ))

        # Column pruning simulation
        self.stdout.write('\nColumn pruning:')
        self.stdout.write('  Query: SUM(amount) GROUP BY customer_email')
        self.stdout.write('  CSV:    must read ALL 5 columns (id, order_number, email, amount, price)')
        needed_cols = ['customer_email', 'amount']
        needed_bytes = sum(
            len(zlib.compress(','.join(columns[c]).encode())) for c in needed_cols
        )
        total_bytes = columnar_compressed_size
        self.stdout.write(self.style.SUCCESS(
            f'  Parquet: reads ONLY {needed_cols} -> {needed_bytes}/{total_bytes} bytes '
            f'({needed_bytes*100//total_bytes}% of data read)'
        ))

        self.stdout.write('\nProduction: write Parquet to S3')
        self.stdout.write('  import pyarrow as pa')
        self.stdout.write('  import pyarrow.parquet as pq')
        self.stdout.write('  table = pa.Table.from_pydict(columns)')
        self.stdout.write('  pq.write_to_dataset(table, root_path="s3://bucket/orders/",')
        self.stdout.write('      partition_cols=["year", "month"], compression="snappy")')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Columnar: 60-90% size reduction with compression')
        self.stdout.write('  - Column pruning: read only needed columns (10-50x less I/O)')
        self.stdout.write('  - Predicate pushdown: skip row groups by min/max statistics')
        self.stdout.write('  - pyarrow + S3: production-grade Parquet pipeline')
