from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q91 PROBLEM: Reprocessing pipeline appends to existing output.
    Re-running adds duplicate rows. Downstream reports show double counts.
    No deduplication or idempotency in the pipeline.
    """
    help = 'Q91 Problem: Pipeline re-run appends duplicates'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q91 PROBLEM: Pipeline re-run appends duplicate rows')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q91-ORD-{i:03}',
                customer_email=f'q91user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        output_store = []  # Simulates append-mode file/table

        def run_pipeline_append():
            """Non-idempotent: appends every run."""
            orders = list(Order.objects.values('id', 'order_number', 'amount'))
            for order in orders:
                output_store.append({'id': order['id'], 'amount': str(order['amount'])})

        self.stdout.write('Run 1 (initial):')
        run_pipeline_append()
        self.stdout.write(f'  Output rows: {len(output_store)}')

        self.stdout.write('Run 2 (reprocess after bug fix):')
        run_pipeline_append()
        self.stdout.write(self.style.ERROR(f'  Output rows: {len(output_store)} <- DUPLICATED!'))

        ids = [r['id'] for r in output_store]
        from collections import Counter
        counts = Counter(ids)
        dupes = {k: v for k, v in counts.items() if v > 1}
        self.stdout.write(self.style.ERROR(
            f'\n  Duplicate IDs: {dupes}'
            f'\n  SUM(amount) = {sum(Decimal(r["amount"]) for r in output_store)}'
            f'\n  Expected:    {sum(Decimal(r["amount"]) for r in output_store[:3])}'
            f'\n  Revenue report is 2× inflated!'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Every pipeline re-run doubles the data'
            '\n  - Bug fix requires reprocessing -> guarantees duplicates'
            '\n  - Downstream analytics report wrong numbers'
            '\n  - Must manually detect and deduplicate after the fact'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Pipelines must be idempotent (re-run = same result)')
        self.stdout.write('  - Use truncate+reload or upsert, never blind append')
        self.stdout.write('  - Track pipeline run ID to detect and prevent double-runs')
        self.stdout.write('  - Test idempotency: run twice, verify same output')
