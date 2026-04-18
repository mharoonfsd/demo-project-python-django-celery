from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q92 PROBLEM: Pipeline scans the full orders table on every run.
    With 1M rows, this means 1M rows read even when only 100 new orders
    arrived since last run. Wastes DB I/O, network, and compute resources.
    """
    help = 'Q92 Problem: Full table scan every run instead of incremental'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q92 PROBLEM: Full table scan every pipeline run')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        from datetime import datetime, timezone
        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q92-ORD-{i:03}',
                customer_email=f'q92user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        def run_full_scan_pipeline():
            """Full scan: always reads ALL rows."""
            all_orders = list(Order.objects.values('id', 'created_at', 'amount'))
            processed = 0
            for order in all_orders:
                # Process every order every run
                processed += 1
            return len(all_orders), processed

        self.stdout.write('Simulated pipeline performance:')
        self.stdout.write('  Scenario: 1M existing orders, 100 new orders since last run')
        self.stdout.write('')

        # Simulate at scale
        total_rows = 1_000_000
        new_rows = 100
        rows_per_second = 10_000  # assumed processing rate

        full_scan_time = total_rows / rows_per_second
        incremental_time = new_rows / rows_per_second

        count, processed = run_full_scan_pipeline()
        self.stdout.write(f'  Full scan reads: {count} existing rows')
        self.stdout.write(self.style.ERROR(
            f'\n  At 1M rows (simulated):'
            f'\n    Full scan time: {full_scan_time:.0f}s = {full_scan_time/60:.1f} minutes'
            f'\n    Rows useful:    {new_rows} ({new_rows*100//total_rows}% of scan)'
            f'\n    Wasted reads:   {total_rows - new_rows:,}'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Full scan grows with total data, not new data'
            '\n  - 1M rows today -> 10M rows in 1 year'
            '\n  - Pipeline gets 10x slower as data accumulates'
            '\n  - DB under constant load from repeated full scans'
            '\n  - Unindexed scan locks tables in some DB configurations'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Track last processed watermark (max created_at or max id)')
        self.stdout.write('  - Next run: only query rows > watermark')
        self.stdout.write('  - Index on created_at for fast watermark queries')
        self.stdout.write('  - Incremental time = O(new data), not O(total data)')
