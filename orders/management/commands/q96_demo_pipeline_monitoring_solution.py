from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q96 SOLUTION: Add row count assertions, historical comparison,
    and metric emission. Fail pipeline if output is anomalous.
    """
    help = 'Q96 Solution: Pipeline monitoring with row count assertions'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q96 SOLUTION: Pipeline monitoring catches silent failures')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q96-SOL-{i:03}',
                customer_email=f'q96sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        MIN_EXPECTED_ROWS = 1
        MAX_DROP_PERCENT = 50  # alert if > 50% fewer rows than previous run
        previous_run_rows = 5   # simulated historical baseline

        metrics = {}

        def emit_metric(name, value):
            metrics[name] = value
            self.stdout.write(f'  METRIC: {name}={value}')

        def run_monitored_pipeline():
            import time
            start = time.monotonic()
            # Correct pipeline
            orders = list(Order.objects.values('id', 'amount'))
            output = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]
            duration_ms = int((time.monotonic() - start) * 1000)
            return output, duration_ms

        self.stdout.write('Running monitored pipeline...')
        result, duration_ms = run_monitored_pipeline()
        row_count = len(result)

        self.stdout.write('\nPipeline metrics:')
        emit_metric('pipeline_row_count', row_count)
        emit_metric('pipeline_duration_ms', duration_ms)

        # Assertion 1: non-empty output
        if row_count < MIN_EXPECTED_ROWS:
            self.stdout.write(self.style.ERROR(
                f'  ALERT: row_count={row_count} < min={MIN_EXPECTED_ROWS} -> PIPELINE FAILED'
            ))
            emit_metric('pipeline_status', 0)
            return

        # Assertion 2: not a huge drop vs previous run
        drop_percent = (previous_run_rows - row_count) / previous_run_rows * 100
        if drop_percent > MAX_DROP_PERCENT:
            self.stdout.write(self.style.ERROR(
                f'  ALERT: {drop_percent:.0f}% drop vs previous run -> investigate'
            ))
            emit_metric('pipeline_anomaly', 1)
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  Row count check: {row_count} rows (prev={previous_run_rows}, '
                f'drop={max(0,drop_percent):.0f}%) -> OK'
            ))
            emit_metric('pipeline_anomaly', 0)

        emit_metric('pipeline_status', 1)
        self.stdout.write(self.style.SUCCESS(f'\n  Pipeline completed successfully: {row_count} rows'))

        # Demonstrate catching the silent-failure scenario
        self.stdout.write('\nDemo: catching 0-row output:')
        try:
            empty_result = []
            assert len(empty_result) >= MIN_EXPECTED_ROWS, (
                f'Pipeline output too small: {len(empty_result)} rows < {MIN_EXPECTED_ROWS} expected'
            )
        except AssertionError as e:
            self.stdout.write(self.style.ERROR(f'  AssertionError: {e}'))
            self.stdout.write(self.style.ERROR('  -> Pipeline exits with non-zero code -> CloudWatch alarm fires'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Assert row_count > MIN_EXPECTED after every pipeline run')
        self.stdout.write('  - Compare to previous run baseline (alert on > 50% drop)')
        self.stdout.write('  - Emit row_count and status metrics to CloudWatch')
        self.stdout.write('  - CloudWatch alarm: trigger PagerDuty if row_count = 0')
