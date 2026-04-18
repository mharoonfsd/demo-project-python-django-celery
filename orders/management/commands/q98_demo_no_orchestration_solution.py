from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q98 SOLUTION: Implement checkpointing and retry for pipeline steps.
    Track step status. On failure, retry from failed step only.
    Show Step Functions-style state machine pattern.
    """
    help = 'Q98 Solution: Orchestration with checkpoints and retry'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q98 SOLUTION: Orchestration with checkpoints and step retry')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q98-SOL-{i:03}',
                customer_email=f'q98sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        import json
        import tempfile
        import os

        checkpoint_dir = tempfile.mkdtemp()

        def save_checkpoint(step_name, data):
            path = os.path.join(checkpoint_dir, f'{step_name}.json')
            with open(path, 'w') as f:
                json.dump(data, f, default=str)
            self.stdout.write(f'    Checkpoint saved: {step_name}')

        def load_checkpoint(step_name):
            path = os.path.join(checkpoint_dir, f'{step_name}.json')
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
            return None

        def with_retry(fn, max_attempts=3, step_name=''):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn()
                except Exception as e:
                    if attempt < max_attempts:
                        self.stdout.write(
                            f'    Attempt {attempt} failed: {e}. Retrying...'
                        )
                    else:
                        raise

        # Attempt counter to simulate transient failure then success
        attempt_counter = {'step2': 0}

        def step_1():
            cached = load_checkpoint('step1')
            if cached:
                self.stdout.write(self.style.WARNING('  Step 1: loaded from checkpoint (skipped)'))
                return cached
            orders = list(Order.objects.values('id', 'amount'))
            data = [{'id': o['id'], 'amount': str(o['amount'])} for o in orders]
            save_checkpoint('step1', data)
            return data

        def step_2(data):
            cached = load_checkpoint('step2')
            if cached:
                self.stdout.write(self.style.WARNING('  Step 2: loaded from checkpoint (skipped)'))
                return cached
            attempt_counter['step2'] += 1
            if attempt_counter['step2'] < 3:
                raise ConnectionError('S3 timeout (transient)')
            result = [{'id': r['id'], 'amount_usd': r['amount']} for r in data]
            save_checkpoint('step2', result)
            return result

        def step_3(data):
            return len(data)

        self.stdout.write('Pipeline run with checkpointing and retry:')
        try:
            self.stdout.write('  Step 1: Extract')
            data1 = step_1()
            self.stdout.write(self.style.SUCCESS(f'    {len(data1)} records'))

            self.stdout.write('  Step 2: Transform (with retry)')
            data2 = with_retry(lambda: step_2(data1), max_attempts=3, step_name='step2')
            self.stdout.write(self.style.SUCCESS(f'    {len(data2)} records'))

            self.stdout.write('  Step 3: Load')
            count = step_3(data2)
            self.stdout.write(self.style.SUCCESS(f'    Loaded {count} records'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Pipeline failed: {e}'))

        self.stdout.write('\nSimulating restart (checkpoints present):')
        attempt_counter['step2'] = 999  # step 2 now succeeds immediately
        data1 = step_1()    # loads from checkpoint
        data2 = step_2(data1)  # loads from checkpoint
        self.stdout.write(self.style.SUCCESS('  Restart skipped completed steps via checkpoints'))

        # Cleanup
        import shutil
        shutil.rmtree(checkpoint_dir)

        self.stdout.write('\nProduction orchestrators:')
        self.stdout.write('  - AWS Step Functions: managed state machine, built-in retry')
        self.stdout.write('  - Apache Airflow: DAG-based, rich UI, complex dependencies')
        self.stdout.write('  - Prefect / Dagster: Python-native, modern observability')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Checkpoint step output before proceeding')
        self.stdout.write('  - Retry transient errors with backoff')
        self.stdout.write('  - Restart from failed step, not beginning')
        self.stdout.write('  - Use orchestrator (Airflow, Step Functions) in production')
