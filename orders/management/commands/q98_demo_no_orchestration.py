from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q98 PROBLEM: Pipeline has no orchestration or retry logic. If step 2
    of a 3-step pipeline fails, there is no automatic retry, no DAG, and
    no way to restart from the failed step. Must redo all work from scratch.
    """
    help = 'Q98 Problem: No orchestration - partial failure requires full restart'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q98 PROBLEM: No orchestration - partial failure = full restart')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q98-ORD-{i:03}',
                customer_email=f'q98user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        def step_1_extract():
            """Step 1: Extract (takes 30 minutes at scale)."""
            orders = list(Order.objects.values('id', 'amount'))
            return orders

        def step_2_transform(data):
            """Step 2: Transform (fails due to a transient error)."""
            raise ConnectionError('S3 connection timeout (transient)')

        def step_3_load(data):
            """Step 3: Load to data warehouse."""
            return len(data)

        def run_pipeline_no_orchestration():
            self.stdout.write('Step 1: Extract...')
            data = step_1_extract()
            self.stdout.write(self.style.SUCCESS(f'  Step 1 complete: {len(data)} records'))

            self.stdout.write('Step 2: Transform...')
            try:
                transformed = step_2_transform(data)
                self.stdout.write(self.style.SUCCESS('  Step 2 complete'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Step 2 FAILED: {e}'))
                self.stdout.write(self.style.ERROR(
                    '  No retry. No checkpoint. Step 1 results discarded.'
                    '\n  Must restart from Step 1 (30 minutes of work lost)'
                ))
                return False

            self.stdout.write('Step 3: Load...')
            step_3_load(transformed)
            return True

        success = run_pipeline_no_orchestration()

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Linear pipeline with no checkpoints'
            '\n  - Step 2 transient error = restart from Step 1'
            '\n  - No retry with backoff for transient errors'
            '\n  - On-call engineer must manually restart at 2am'
            '\n  - No audit trail of which steps completed'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Checkpoint: save step output before proceeding')
        self.stdout.write('  - Retry transient errors (S3 timeout, network blip)')
        self.stdout.write('  - DAG orchestrator: restart from failed step, not start')
        self.stdout.write('  - Use Airflow, Step Functions, or Prefect for production')
