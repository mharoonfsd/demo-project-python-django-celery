from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q88 SOLUTION: Define schema contracts between pipeline stages.
    Validate at boundaries. Fail fast with helpful errors at stage entry,
    not mid-processing. Use canonical field names across all stages.
    """
    help = 'Q88 Solution: Schema validation at pipeline stage boundaries'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q88 SOLUTION: Schema contracts prevent silent mismatches')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q88-SOL-{i:03}',
                customer_email=f'q88sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Schema definition
        STAGE1_SCHEMA = {'id', 'amount', 'email'}
        STAGE2_SCHEMA = {'id', 'amount_usd'}

        def validate_schema(records, required_keys, stage_name):
            if not records:
                return
            missing = required_keys - set(records[0].keys())
            extra = set(records[0].keys()) - required_keys
            if missing:
                raise ValueError(
                    f'{stage_name}: missing required fields {missing}. '
                    f'Got: {set(records[0].keys())}'
                )

        # Stage 1: Extract with canonical field names
        def stage_1_extract():
            records = [
                {'id': o['id'], 'amount': str(o['amount']), 'email': o['customer_email']}
                for o in Order.objects.values('id', 'amount', 'customer_email')
            ]
            validate_schema(records, STAGE1_SCHEMA, 'Stage 1')
            return records

        # Stage 2: Transform with schema validation at entry
        def stage_2_transform(records):
            validate_schema(records, STAGE1_SCHEMA, 'Stage 2 input')
            results = []
            for record in records:
                results.append({'id': record['id'], 'amount_usd': record['amount']})
            validate_schema(results, STAGE2_SCHEMA, 'Stage 2 output')
            return results

        self.stdout.write('Pipeline with schema validation:')
        try:
            stage1 = stage_1_extract()
            self.stdout.write(self.style.SUCCESS(f'  Stage 1: {len(stage1)} records, schema valid'))

            stage2 = stage_2_transform(stage1)
            self.stdout.write(self.style.SUCCESS(f'  Stage 2: {len(stage2)} records, schema valid'))
            for row in stage2[:2]:
                self.stdout.write(f'    {row}')
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'  Schema error: {e}'))

        # Demo: what happens with mismatched schema
        self.stdout.write('\nDemo: schema validation catches mismatch at stage entry:')
        bad_records = [{'order_id': 1, 'amount': '50.00', 'email': 'test@example.com'}]
        try:
            validate_schema(bad_records, STAGE1_SCHEMA, 'Stage 2 input')
        except ValueError as e:
            self.stdout.write(self.style.WARNING(f'  Caught early: {e}'))

        self.stdout.write('\nProduction: use pydantic for strict schema contracts')
        self.stdout.write('  from pydantic import BaseModel')
        self.stdout.write('  class Stage1Record(BaseModel):')
        self.stdout.write('      id: int')
        self.stdout.write('      amount: str')
        self.stdout.write('      email: str')
        self.stdout.write('  Stage1Record(**record)  # raises ValidationError if wrong')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Validate schema at stage boundaries, not mid-processing')
        self.stdout.write('  - Use canonical field names consistently across stages')
        self.stdout.write('  - Fail fast: catch mismatches before hours of compute')
        self.stdout.write('  - pydantic/marshmallow: type-safe schema contracts')
