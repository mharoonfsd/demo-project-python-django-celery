from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q89 SOLUTION: Write to temp file, then atomically rename to target.
    Rename is atomic on POSIX filesystems. On Windows, use replace().
    On S3, upload to staging prefix then copy to final key.
    """
    help = 'Q89 Solution: Atomic write via temp file and rename'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q89 SOLUTION: Atomic write - temp file + rename')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q89-SOL-{i:03}',
                customer_email=f'q89sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        import os
        import json
        import tempfile

        output_dir = tempfile.gettempdir()
        final_path = os.path.join(output_dir, 'q89_sol_output.json')

        def atomic_write(records, final_path):
            """Write to temp file, then atomically rename to final path."""
            # Write to temp file in SAME directory (rename across filesystems fails)
            dir_name = os.path.dirname(final_path)
            tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
            try:
                with os.fdopen(tmp_fd, 'w') as f:
                    json.dump(records, f)
                # Atomic rename: either complete or not — no partial state
                os.replace(tmp_path, final_path)  # os.replace() works on Windows too
                return True
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise

        orders = list(Order.objects.values('id', 'amount'))
        records = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]

        self.stdout.write(f'Writing {len(records)} records atomically...')
        atomic_write(records, final_path)
        self.stdout.write(self.style.SUCCESS(f'  Written to: {final_path}'))

        # Verify
        with open(final_path) as f:
            loaded = json.load(f)
        self.stdout.write(self.style.SUCCESS(f'  Read back: {len(loaded)} records — valid JSON'))
        os.remove(final_path)

        self.stdout.write('\nHow atomic rename works:')
        self.stdout.write('  1. Write all data to /tmp/output_abc123.tmp')
        self.stdout.write('  2. os.replace(tmp_path, final_path)')
        self.stdout.write('     - On success: final_path is atomically updated')
        self.stdout.write('     - On crash before step 2: final_path unchanged')
        self.stdout.write('     - POSIX: rename() is atomic (single directory entry swap)')

        self.stdout.write('\nS3 equivalent (atomic pattern):')
        self.stdout.write('  # Upload to staging prefix')
        self.stdout.write('  s3.upload_file("data.json", "bucket", "staging/orders/data.json")')
        self.stdout.write('  # Copy to final location (atomic in S3 terms)')
        self.stdout.write('  s3.copy({"Bucket": "bucket", "Key": "staging/orders/data.json"},')
        self.stdout.write('          "bucket", "output/orders/data.json")')
        self.stdout.write('  # Delete staging')
        self.stdout.write('  s3.delete_object(Bucket="bucket", Key="staging/orders/data.json")')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Write to temp file in SAME directory as final path')
        self.stdout.write('  - os.replace() is atomic rename on all platforms')
        self.stdout.write('  - On crash: old file intact; no partial state')
        self.stdout.write('  - Consumers always see either old or new complete file')
