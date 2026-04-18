from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q93 PROBLEM: All pipeline output goes into a single monolithic file.
    Any query must scan the entire file. Partitioning by date/region would
    allow query engines to skip irrelevant data entirely.
    """
    help = 'Q93 Problem: No partitioning - full file scan for every query'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q93 PROBLEM: Single file - no partitioning, full scan always')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        import json
        import tempfile
        import os

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q93-ORD-{i:03}',
                customer_email=f'q93user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # All data in one file
        orders = list(Order.objects.values('id', 'order_number', 'amount', 'created_at'))
        all_records = [
            {'id': o['id'], 'amount': str(o['amount']), 'date': str(o['created_at'])[:10]}
            for o in orders
        ]

        tmp_dir = tempfile.mkdtemp()
        mono_path = os.path.join(tmp_dir, 'output.json')
        with open(mono_path, 'w') as f:
            json.dump(all_records, f)

        file_size = os.path.getsize(mono_path)

        self.stdout.write(f'Monolithic output file: {file_size} bytes, {len(all_records)} records')

        # Query: "orders for 2024-01-15 only"
        with open(mono_path) as f:
            all_data = json.load(f)

        today = all_records[0]['date'] if all_records else '2024-01-15'
        matches = [r for r in all_data if r['date'] == today]

        self.stdout.write(self.style.ERROR(
            f'\nQuery: orders for date={today}'
            f'\n  Records scanned: {len(all_data)} (ALL records in file)'
            f'\n  Records matched: {len(matches)}'
            f'\n  Useful work:     {len(matches)*100//max(len(all_data),1)}%'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: At scale (1B rows, 3 years of data)'
            '\n  - Every query scans all 1B rows'
            '\n  - Query for "last week" reads 3 years of data'
            '\n  - Storage is unorganized blob'
            '\n  - Athena/Redshift charges per byte scanned'
        ))

        os.remove(mono_path)
        os.rmdir(tmp_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Partition data by query patterns (date, region, status)')
        self.stdout.write('  - Partition pruning: skip entire partitions at query time')
        self.stdout.write('  - Athena: pays per byte scanned — partitioning saves money')
        self.stdout.write('  - Common partition: year=/month=/day= for time-series data')
