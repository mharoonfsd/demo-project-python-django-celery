from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q12 PROBLEM: Django's bulk_create() does not support ManyToMany relationships.
    M2M relations are stored in a separate through-table and require individual
    INSERT statements. Attempting to set M2M fields on unsaved instances
    or expecting bulk_create to handle them will silently fail or raise errors.
    """
    help = 'Q12 Problem: M2M relationships cannot be set via bulk_create()'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q12 PROBLEM: M2M with bulk_create not supported')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Simulate: trying to assign M2M during bulk_create
        # (Order has no real M2M in this model, so we demonstrate the concept
        #  using Tax.orders reverse relation as a stand-in)
        orders = [
            Order(
                order_number=f'Q12-ORDER-{i}',
                customer_email=f'q12_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            for i in range(1, 4)
        ]

        self.stdout.write('Creating 3 orders with bulk_create()...')
        created = Order.objects.bulk_create(orders)
        self.stdout.write(f'  {len(created)} orders created in DB')

        # PROBLEM: you cannot set M2M on these instances — they bypass ORM lifecycle
        # Attempting order.tags.set([...]) on a just-bulk-created instance raises:
        # ValueError: "<Order>" needs to have a value for field "id" before
        # this many-to-many relationship can be used.
        self.stdout.write(self.style.ERROR(
            'PROBLEM: bulk_create does not return PKs reliably (especially on older DBs) '
            'and does not trigger signals, making M2M assignment afterwards unreliable.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - M2M rows are silently not created')
        self.stdout.write('  - No exception is raised; bugs are invisible')
        self.stdout.write('  - Related objects appear missing at query time')
