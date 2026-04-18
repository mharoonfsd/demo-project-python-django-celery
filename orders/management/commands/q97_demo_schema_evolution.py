from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q97 PROBLEM: Pipeline has no schema evolution strategy. Dev removes
    the 'price' column from pipeline output. Downstream consumer that reads
    'price' breaks with KeyError. Breaking change deployed without coordination.
    """
    help = 'Q97 Problem: Breaking schema change breaks downstream consumers'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q97 PROBLEM: Schema evolution - breaking column removal')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q97-ORD-{i:03}',
                customer_email=f'q97user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('90.00'),
            )

        def pipeline_v1_output():
            """V1 schema: includes 'price' field."""
            return [
                {'id': o['id'], 'amount': str(o['amount']), 'price': str(o['price'])}
                for o in Order.objects.values('id', 'amount', 'price')
            ]

        def pipeline_v2_output():
            """V2 schema: 'price' removed (breaking change!)."""
            return [
                {'id': o['id'], 'amount': str(o['amount'])}  # 'price' removed
                for o in Order.objects.values('id', 'amount')
            ]

        def downstream_consumer(records):
            """Consumer expects 'price' field."""
            for record in records:
                margin = Decimal(record['amount']) - Decimal(record['price'])  # KeyError!
                pass

        self.stdout.write('V1 pipeline + consumer: working')
        v1 = pipeline_v1_output()
        try:
            downstream_consumer(v1)
            self.stdout.write(self.style.SUCCESS('  V1 consumer: OK'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'  V1 consumer: KeyError {e}'))

        self.stdout.write('\nV2 pipeline deployed (removed price field):')
        v2 = pipeline_v2_output()
        try:
            downstream_consumer(v2)
        except KeyError as e:
            self.stdout.write(self.style.ERROR(
                f'  V2 consumer: KeyError {e}'
                f'\n  Consumer broken after pipeline deploy'
                f'\n  No warning, no migration path, no version in schema'
            ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Uncoordinated breaking schema change'
            '\n  - Consumer deployed before or after producer change = broken window'
            '\n  - No schema versioning to detect incompatibilities'
            '\n  - No deprecation period for consumers to migrate'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Additive changes (add field) are non-breaking')
        self.stdout.write('  - Removing/renaming fields is breaking — coordinate first')
        self.stdout.write('  - Deprecate: add new field, keep old, remove after migration')
        self.stdout.write('  - Use schema registry (Confluent, Glue) for enforcement')
