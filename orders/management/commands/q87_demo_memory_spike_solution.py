from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q87 SOLUTION: Use .iterator() for streaming. Use chunked processing
    with id-based pagination. Use .values() to avoid model instantiation.
    Constant memory regardless of dataset size.
    """
    help = 'Q87 Solution: Streaming and chunked processing for large datasets'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q87 SOLUTION: Constant-memory processing with iterator/chunks')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q87-SOL-{i:03}',
                customer_email=f'q87sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Method 1: .iterator()
        self.stdout.write('Method 1: QuerySet.iterator() (server-side cursor)')
        total = Decimal('0.00')
        count = 0
        for order in Order.objects.values('id', 'amount').iterator(chunk_size=1000):
            total += order['amount']
            count += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Processed {count} orders, total={total} — constant memory use'
        ))
        self.stdout.write('  Memory: only chunk_size rows in RAM at a time')

        # Method 2: ID-based chunked pagination
        self.stdout.write('\nMethod 2: ID-based chunked pagination')
        CHUNK_SIZE = 3
        last_id = 0
        chunk_num = 0
        total_chunked = Decimal('0.00')
        while True:
            chunk = list(
                Order.objects.filter(id__gt=last_id)
                .values('id', 'amount')
                .order_by('id')[:CHUNK_SIZE]
            )
            if not chunk:
                break
            chunk_num += 1
            chunk_total = sum(row['amount'] for row in chunk)
            total_chunked += chunk_total
            last_id = chunk[-1]['id']
            self.stdout.write(
                f'  Chunk {chunk_num}: {len(chunk)} rows, ids {chunk[0]["id"]}-{last_id}'
            )
        self.stdout.write(self.style.SUCCESS(
            f'  Total={total_chunked} in {chunk_num} chunks of {CHUNK_SIZE}'
        ))

        self.stdout.write('\nMethod 3: .values() to avoid model instantiation overhead')
        self.stdout.write('  # Bad: Order objects (large, ~500 bytes each)')
        self.stdout.write('  for order in Order.objects.all():  # loads full model')
        self.stdout.write('  # Good: dicts (small, ~100 bytes each)')
        self.stdout.write('  for row in Order.objects.values("id", "amount").iterator():')
        self.stdout.write('      pass  # 5x less memory than full model objects')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - .iterator(): streams rows, constant memory')
        self.stdout.write('  - ID pagination: restartable, works on all DBs')
        self.stdout.write('  - .values("id","amount"): avoid loading unused columns')
        self.stdout.write('  - Combine: .values(...).iterator(chunk_size=1000)')
