from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q99 SOLUTION: Use _SUCCESS flag file to signal pipeline completion.
    Reader waits for _SUCCESS before reading data files. Clean up temp
    files on failure. Atomic write prevents partial reads.
    """
    help = 'Q99 Solution: _SUCCESS flag coordinates writer and reader'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q99 SOLUTION: _SUCCESS flag eliminates pipeline race condition')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q99-SOL-{i:03}',
                customer_email=f'q99sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        import os
        import json
        import tempfile

        output_dir = tempfile.mkdtemp()
        data_file = os.path.join(output_dir, 'orders.json')
        success_flag = os.path.join(output_dir, '_SUCCESS')
        tmp_data_file = data_file + '.tmp'

        def writer_with_flag():
            """Write data atomically, then write _SUCCESS flag."""
            try:
                orders = list(Order.objects.values('id', 'amount'))
                records = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]

                # Write to temp file first
                with open(tmp_data_file, 'w') as f:
                    json.dump(records, f)

                # Atomic rename
                os.replace(tmp_data_file, data_file)

                # Signal completion AFTER all data files are written
                with open(success_flag, 'w') as f:
                    import json as _json
                    _json.dump({'row_count': len(records)}, f)

                return len(records)
            except Exception:
                # Clean up temp files on failure
                for path in [tmp_data_file]:
                    if os.path.exists(path):
                        os.remove(path)
                raise

        def reader_with_flag(timeout_checks=3):
            """Only reads data if _SUCCESS flag is present."""
            for check in range(timeout_checks):
                if os.path.exists(success_flag):
                    with open(success_flag) as f:
                        meta = json.load(f)
                    with open(data_file) as f:
                        records = json.load(f)
                    return records, meta
                self.stdout.write(f'  Reader: waiting for _SUCCESS flag (check {check+1})')
            return None, None

        self.stdout.write('Writer: exporting orders...')
        count = writer_with_flag()
        self.stdout.write(self.style.SUCCESS(f'  Writer: {count} records written'))
        self.stdout.write(self.style.SUCCESS(f'  Writer: _SUCCESS flag written'))

        self.stdout.write('\nReader: checking for completion...')
        records, meta = reader_with_flag()
        if records:
            self.stdout.write(self.style.SUCCESS(
                f'  Reader: _SUCCESS found! Reading {len(records)} records'
            ))
            self.stdout.write(self.style.SUCCESS(f'  Metadata: {meta}'))
        else:
            self.stdout.write(self.style.ERROR('  Reader: timed out waiting for _SUCCESS'))

        self.stdout.write('\n_SUCCESS on S3:')
        self.stdout.write('  s3://bucket/orders/year=2024/month=01/day=15/_SUCCESS')
        self.stdout.write('  s3://bucket/orders/year=2024/month=01/day=15/part-0001.parquet')
        self.stdout.write('  # Reader: check for _SUCCESS before listing parquet files')
        self.stdout.write('  # Hadoop/Spark: uses _SUCCESS natively')

        # Cleanup
        import shutil
        shutil.rmtree(output_dir)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Write all data files first, _SUCCESS flag last')
        self.stdout.write('  - Reader: do not process partition without _SUCCESS')
        self.stdout.write('  - _SUCCESS can contain metadata: row_count, checksum')
        self.stdout.write('  - Clean up temp files on any failure to avoid stale state')
