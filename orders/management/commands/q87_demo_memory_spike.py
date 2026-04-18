from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q87 PROBLEM: Pipeline loads entire queryset into memory with list().
    For 1M rows this causes memory spike, OOM, or container restart.
    """
    help = 'Q87 Problem: Loading entire queryset into memory causes OOM'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q87 PROBLEM: list(queryset) loads all rows into memory')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q87-ORD-{i:03}',
                customer_email=f'q87user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import sys

        def process_all_no_streaming():
            """Loads all records into memory at once."""
            all_orders = list(Order.objects.all())  # PROBLEM: forces full eval
            total = sum(float(o.amount) for o in all_orders)
            return len(all_orders), total

        count, total = process_all_no_streaming()
        single_order_bytes = sys.getsizeof(Order.objects.get(pk=Order.objects.first().pk))

        self.stdout.write(f'Loaded {count} orders into memory at once')
        self.stdout.write(f'Approx memory per Order object: ~{single_order_bytes} bytes')
        self.stdout.write(f'Estimated for 1M rows: ~{single_order_bytes * 1_000_000 // 1024 // 1024} MB')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: list(Order.objects.all()) with 1M rows'
            '\n  - All rows fetched in single DB query'
            '\n  - All Python objects kept in RAM simultaneously'
            '\n  - 1M rows × ~500 bytes = ~500MB RAM spike'
            '\n  - ECS container OOM kill (exit code 137)'
            '\n  - Entire pipeline fails; must reprocess from scratch'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Never use list() on large querysets in pipelines')
        self.stdout.write('  - Use .iterator() for server-side cursor streaming')
        self.stdout.write('  - Use chunked processing with id pagination')
        self.stdout.write('  - Only load what you need (values(), defer())')
