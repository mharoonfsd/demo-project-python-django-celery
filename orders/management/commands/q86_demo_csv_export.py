from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q86 PROBLEM: Pipeline exports data as CSV (row-oriented, uncompressed).
    Large exports are slow and expensive. Reading back requires parsing all
    columns even when only a few are needed.
    """
    help = 'Q86 Problem: CSV export instead of columnar format with compression'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q86 PROBLEM: CSV export - slow, large, no column pruning')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q86-ORD-{i:03}',
                customer_email=f'q86user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        import csv
        import io

        # Simulate exporting ALL columns to CSV (no column pruning possible)
        orders = list(Order.objects.values(
            'id', 'order_number', 'customer_email', 'amount',
            'price', 'total', 'created_at', 'tax_id'
        ))

        output = io.StringIO()
        if orders:
            writer = csv.DictWriter(output, fieldnames=orders[0].keys())
            writer.writeheader()
            for row in orders:
                row['created_at'] = str(row['created_at'])
                writer.writerow(row)
        csv_content = output.getvalue()

        row_count = len(orders)
        col_count = len(orders[0]) if orders else 0
        csv_bytes = len(csv_content.encode('utf-8'))

        self.stdout.write(f'Exported {row_count} rows × {col_count} columns')
        self.stdout.write(f'CSV size: {csv_bytes} bytes (uncompressed)')
        self.stdout.write(f'CSV size (extrapolated to 1M rows): ~{csv_bytes * 200000 // 1024 // 1024} MB')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: CSV at scale'
            '\n  Query: "SUM(amount) by customer_email"'
            '\n  CSV: must read ALL 8 columns just to use 2'
            '\n  - No compression: 1M rows ~ 500MB on disk'
            '\n  - Row-oriented: cannot skip unused columns during read'
            '\n  - No statistics: full scan required for every query'
            '\n  - S3 storage costs and transfer costs are higher'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - CSV: simple but not suitable for analytics at scale')
        self.stdout.write('  - Parquet: columnar, compressed, with statistics')
        self.stdout.write('  - Column pruning: read only needed columns')
        self.stdout.write('  - Predicate pushdown: skip row groups by statistics')
