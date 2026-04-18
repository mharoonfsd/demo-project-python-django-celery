from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q97 SOLUTION: Backward-compatible schema evolution. Keep old fields
    during transition, add new fields additively, deprecate with warning,
    remove only after all consumers migrate.
    """
    help = 'Q97 Solution: Backward-compatible schema evolution with deprecation'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q97 SOLUTION: Safe schema evolution - additive changes')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q97-SOL-{i:03}',
                customer_email=f'q97sol{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('90.00'),
            )

        def pipeline_v2_backward_compatible():
            """V2: new field 'unit_price' added, old 'price' kept during transition."""
            return [
                {
                    'id': o['id'],
                    'amount': str(o['amount']),
                    'price': str(o['price']),       # kept for backward compat
                    'unit_price': str(o['price']),  # new canonical name (additive)
                    '_schema_version': 2,
                }
                for o in Order.objects.values('id', 'amount', 'price')
            ]

        def consumer_v1(records):
            """Old consumer: still reads 'price'."""
            for record in records:
                _ = Decimal(record['price'])  # still works!

        def consumer_v2(records):
            """New consumer: reads 'unit_price' with fallback."""
            for record in records:
                price = record.get('unit_price') or record.get('price')
                _ = Decimal(price)

        self.stdout.write('V2 pipeline (backward-compatible):')
        v2 = pipeline_v2_backward_compatible()
        self.stdout.write(f'  Sample record: {v2[0]}')

        self.stdout.write('\nConsumer compatibility:')
        try:
            consumer_v1(v2)
            self.stdout.write(self.style.SUCCESS('  Consumer V1 (reads "price"): OK <- no breakage'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'  Consumer V1: BROKEN {e}'))

        try:
            consumer_v2(v2)
            self.stdout.write(self.style.SUCCESS('  Consumer V2 (reads "unit_price"): OK'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'  Consumer V2: BROKEN {e}'))

        self.stdout.write('\nSafe schema evolution steps:')
        steps = [
            ('Step 1', 'Add new field "unit_price" alongside old "price" (additive)'),
            ('Step 2', 'Notify consumers: "price" deprecated, migrate to "unit_price"'),
            ('Step 3', 'Monitor which consumers still read "price" (access logs)'),
            ('Step 4', 'After all consumers migrated: remove "price" in V3'),
        ]
        for step, desc in steps:
            self.stdout.write(self.style.SUCCESS(f'  {step}: {desc}'))

        self.stdout.write('\nBreaking vs non-breaking changes:')
        self.stdout.write('  NON-BREAKING (safe): add field, widen type (int->bigint)')
        self.stdout.write('  BREAKING (unsafe):   remove field, rename field, narrow type')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Additive changes are always safe: just add new fields')
        self.stdout.write('  - Keep old fields during deprecation window (weeks/months)')
        self.stdout.write('  - Use _schema_version field for consumers to detect version')
        self.stdout.write('  - Schema registry enforces compatibility automatically')
