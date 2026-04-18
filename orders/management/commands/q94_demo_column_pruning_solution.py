from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q94 SOLUTION: Use .values() to select only needed columns.
    Use .only() or .defer() when model methods needed. Show
    query efficiency improvement.
    """
    help = 'Q94 Solution: Column pruning with .values() and .only()'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q94 SOLUTION: Column pruning - fetch only what you need')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q94-SOL-{i:03}',
                customer_email=f'q94sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import sys
        from collections import defaultdict

        # Method 1: .values() - returns dicts, only needed columns
        self.stdout.write('Method 1: .values() - dicts with selected columns')
        pruned = list(Order.objects.values('customer_email', 'amount'))
        pruned_size = sum(sys.getsizeof(row) for row in pruned)
        self.stdout.write(self.style.SUCCESS(f'  Fetched {len(pruned)} rows, ~{pruned_size} bytes'))
        self.stdout.write(f'  Sample: {pruned[0]}')

        # Aggregate in Python
        totals = defaultdict(Decimal)
        for row in pruned:
            totals[row['customer_email']] += row['amount']
        self.stdout.write(f'  SUM(amount) per customer: {dict(totals)}')

        # Method 2: DB aggregation (even better - no Python loop)
        self.stdout.write('\nMethod 2: DB-side aggregation (best)')
        from django.db.models import Sum
        db_totals = list(
            Order.objects.values('customer_email')
            .annotate(total=Sum('amount'))
            .order_by('customer_email')
        )
        self.stdout.write(self.style.SUCCESS('  SELECT customer_email, SUM(amount) FROM orders GROUP BY customer_email'))
        for row in db_totals:
            self.stdout.write(self.style.SUCCESS(f'  {row}'))

        # Method 3: .only() when model methods needed
        self.stdout.write('\nMethod 3: .only() when model instance needed')
        self.stdout.write('  # Fetches only specified columns, lazy-loads rest if accessed')
        self.stdout.write('  orders = Order.objects.only("customer_email", "amount")')
        self.stdout.write('  # Accessing o.order_number triggers extra DB query (N+1 risk)')
        self.stdout.write('  # Use only when you genuinely need model methods')

        self.stdout.write('\nColumn efficiency comparison (1M rows, 8 columns):')
        ALL_COLUMNS = 8
        NEEDED_COLUMNS = 2
        self.stdout.write(f'  SELECT *:                  8 columns, ~500MB transferred')
        self.stdout.write(self.style.SUCCESS(
            f'  SELECT email, amount:      2 columns, ~{500*NEEDED_COLUMNS//ALL_COLUMNS}MB transferred '
            f'({(ALL_COLUMNS - NEEDED_COLUMNS)*100//ALL_COLUMNS}% reduction)'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'  GROUP BY in DB:            0 bytes per row, just aggregate result'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - .values("col1", "col2"): fastest, returns dicts')
        self.stdout.write('  - .only("col1", "col2"): returns models, lazy-loads rest')
        self.stdout.write('  - DB aggregation: push GROUP BY/SUM to the database')
        self.stdout.write('  - Never SELECT * in production pipelines')
