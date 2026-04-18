from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q99 PROBLEM: Pipeline writes to S3 but uses eventual consistency assumptions.
    Race condition: reader checks for file existence, file not yet visible,
    returns empty result. Also: no cleanup of temp files on failure leaves
    partial state that confuses subsequent runs.
    """
    help = 'Q99 Problem: Race condition in pipeline - reader sees stale/empty data'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q99 PROBLEM: Pipeline race condition - reader sees stale data')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q99-ORD-{i:03}',
                customer_email=f'q99user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        import os
        import tempfile
        import json

        output_dir = tempfile.mkdtemp()
        output_file = os.path.join(output_dir, 'orders.json')
        ready_flag = os.path.join(output_dir, '_SUCCESS')

        def writer_without_flag():
            """Writes data file but no completion signal."""
            orders = list(Order.objects.values('id', 'amount'))
            records = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]
            with open(output_file, 'w') as f:
                json.dump(records, f)
            # No _SUCCESS flag written!

        def reader_without_flag():
            """Checks for file without waiting for completion signal."""
            if os.path.exists(output_file):
                with open(output_file) as f:
                    content = f.read()
                if not content.strip():
                    return []  # empty during write!
                return json.loads(content)
            return []  # not found yet

        self.stdout.write('Scenario: writer and reader run concurrently (no flag):')
        self.stdout.write('  Writer: started writing orders.json...')
        self.stdout.write('  Reader: checking for orders.json...')
        self.stdout.write(self.style.ERROR(
            '  Reader: file exists (partially written) -> reads empty/partial data'
            '\n  Reader: reports 0 orders processed'
            '\n  Writer: finishes writing 3 orders'
            '\n  Reader: never re-checks, already reported 0'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No coordination between writer and reader'
            '\n  - File existence != write complete'
            '\n  - S3 strong read-after-write (since 2020) but local/EFS still racy'
            '\n  - Temp files from failed runs confuse next run'
            '\n  - No way to distinguish "writing" from "written" from "failed"'
        ))

        # Cleanup
        import shutil
        shutil.rmtree(output_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Write _SUCCESS flag after all data files written')
        self.stdout.write('  - Reader waits for _SUCCESS before reading data')
        self.stdout.write('  - Clean up temp files on pipeline failure')
        self.stdout.write('  - Use atomic write + rename (see Q89) to eliminate partial reads')
