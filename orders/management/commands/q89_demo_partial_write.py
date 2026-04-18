from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q89 PROBLEM: Pipeline writes directly to the target file. If it crashes
    mid-write, the target file is partially written and corrupt. Downstream
    consumers read corrupt data. There is no way to know if the file is complete.
    """
    help = 'Q89 Problem: Direct write to target file - crash leaves corrupt output'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q89 PROBLEM: Direct file write - partial write on crash = corrupt file')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q89-ORD-{i:03}',
                customer_email=f'q89user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import os
        import json
        import tempfile

        output_path = os.path.join(tempfile.gettempdir(), 'q89_output.json')

        def export_direct_write_with_crash(orders):
            """Writes directly to target — crash leaves partial file."""
            with open(output_path, 'w') as f:
                f.write('[\n')
                for i, order in enumerate(orders):
                    record = {'id': order['id'], 'amount': str(order['amount'])}
                    if i == 3:  # Simulate crash mid-write
                        raise RuntimeError('Out of disk space (simulated crash)')
                    f.write(json.dumps(record) + ',\n')
                f.write(']')

        orders = list(Order.objects.values('id', 'amount'))
        self.stdout.write(f'Writing {len(orders)} orders to {output_path}...')

        try:
            export_direct_write_with_crash(orders)
        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(f'  Pipeline crashed: {e}'))

        # Check what was written
        if os.path.exists(output_path):
            with open(output_path) as f:
                partial_content = f.read()
            self.stdout.write(self.style.ERROR(
                f'\n  CORRUPT FILE at {output_path}:'
                f'\n  {partial_content[:200]}'
                f'\n  File exists but is invalid JSON (truncated mid-write)'
            ))
            os.remove(output_path)

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Downstream consumer reads corrupt file'
            '\n  - json.loads() raises JSONDecodeError'
            '\n  - No way to distinguish complete vs partial write'
            '\n  - Pipeline must be manually restarted'
            '\n  - S3 multipart uploads have same risk without atomic rename'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Never write directly to the target path')
        self.stdout.write('  - Write to temp file, then atomic rename/move')
        self.stdout.write('  - On S3: complete multipart upload or use copy-then-delete')
        self.stdout.write('  - Partial files are indistinguishable from complete files')
