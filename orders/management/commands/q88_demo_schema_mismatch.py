from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q88 PROBLEM: Pipeline stage 1 outputs records with key 'order_id'.
    Pipeline stage 2 expects key 'id'. This schema mismatch causes a KeyError
    at runtime, potentially hours into a long pipeline run.
    """
    help = 'Q88 Problem: Schema mismatch between pipeline stages causes KeyError'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q88 PROBLEM: Schema mismatch - KeyError hours into pipeline')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q88-ORD-{i:03}',
                customer_email=f'q88user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Stage 1: Extract - outputs 'order_id' (old field name)
        def stage_1_extract():
            return [
                {'order_id': o['id'], 'amount': str(o['amount']), 'email': o['customer_email']}
                for o in Order.objects.values('id', 'amount', 'customer_email')
            ]

        # Stage 2: Transform - expects 'id' (new field name)
        def stage_2_transform(records):
            results = []
            for record in records:
                order_id = record['id']   # BUG: key is 'order_id', not 'id'
                results.append({'id': order_id, 'amount_usd': record['amount']})
            return results

        self.stdout.write('Stage 1 output (uses "order_id"):')
        stage1_output = stage_1_extract()
        for row in stage1_output[:2]:
            self.stdout.write(f'  {row}')

        self.stdout.write('\nStage 2 processing (expects "id"):')
        try:
            stage_2_transform(stage1_output)
        except KeyError as e:
            self.stdout.write(self.style.ERROR(
                f'  KeyError: {e}'
                f'\n  Pipeline crashed after running for hours'
                f'\n  All progress lost — must restart from scratch'
            ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Schema changed in stage 1 but stage 2 not updated'
            '\n  - No contract/schema enforcement between stages'
            '\n  - Failure discovered at runtime, not at deploy time'
            '\n  - Long pipelines: wasted hours of compute before crash'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Define explicit schema contracts between pipeline stages')
        self.stdout.write('  - Validate schema at stage boundaries (pydantic/marshmallow)')
        self.stdout.write('  - Use .get() with default or raise helpful error')
        self.stdout.write('  - Test pipeline end-to-end with real schema in CI')
