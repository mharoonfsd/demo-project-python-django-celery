from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q94 PROBLEM: Pipeline queries SELECT * fetching all columns.
    Only 2-3 columns are actually used. Wasted network bandwidth and
    memory moving unused data from DB to pipeline worker.
    """
    help = 'Q94 Problem: SELECT * fetches all columns, only 2-3 needed'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q94 PROBLEM: SELECT * - fetching all columns when 2 needed')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q94-ORD-{i:03}',
                customer_email=f'q94user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import sys

        # Bad: load all columns (Order objects = all fields)
        all_orders = list(Order.objects.all())
        full_object_size = sum(sys.getsizeof(o.__dict__) for o in all_orders)

        # Task only needs: customer_email and amount
        # But we fetched: id, order_number, customer_email, amount, price, total, created_at, tax_id

        ALL_COLUMNS = ['id', 'order_number', 'customer_email', 'amount', 'price', 'total', 'created_at', 'tax_id']
        NEEDED_COLUMNS = ['customer_email', 'amount']

        self.stdout.write(f'Query: "SUM(amount) GROUP BY customer_email"')
        self.stdout.write(f'Columns needed:  {NEEDED_COLUMNS}')
        self.stdout.write(f'Columns fetched: {ALL_COLUMNS}')
        self.stdout.write(f'Columns wasted:  {[c for c in ALL_COLUMNS if c not in NEEDED_COLUMNS]}')
        self.stdout.write(f'')
        self.stdout.write(f'Data transferred from DB (5 rows, all columns):')
        self.stdout.write(self.style.ERROR(f'  Full object sizes: ~{full_object_size} bytes'))

        # Scale estimate
        needed_fraction = len(NEEDED_COLUMNS) / len(ALL_COLUMNS)
        self.stdout.write(self.style.ERROR(
            f'\nAt scale (1M rows):'
            f'\n  SELECT * data volume: ~500MB'
            f'\n  SELECT email, amount: ~{int(500 * needed_fraction)}MB'
            f'\n  Wasted: ~{int(500 * (1-needed_fraction))}MB per pipeline run'
            f'\n  - Slower query (more data from disk)'
            f'\n  - Higher network cost (RDS -> ECS)'
            f'\n  - More memory required in pipeline worker'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use .values("col1", "col2") for pipeline queries')
        self.stdout.write('  - Avoid loading full Django model objects for large scans')
        self.stdout.write('  - Columnar formats (Parquet) benefit from column pruning natively')
        self.stdout.write('  - Index covers: index on (email, amount) = index-only scan')
