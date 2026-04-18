from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q12 SOLUTION: Create objects individually with save() (or bulk_create
    to get PKs, then set M2M separately after). For true M2M, use
    obj.m2m_field.add() or .set() after the object has been saved and has a PK.
    """
    help = 'Q12 Solution: Create objects with save() then assign M2M separately'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q12 SOLUTION: Correct M2M creation pattern')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # SOLUTION 1: Use save() individually so each object has a PK
        self.stdout.write('--- Solution 1: save() each object to get PK first ---')
        saved_orders = []
        for i in range(1, 4):
            order = Order.objects.create(
                order_number=f'Q12-SOL-ORDER-{i}',
                customer_email=f'q12sol_{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            saved_orders.append(order)
            # Now safe to call order.m2m_field.add(...) because PK exists
        self.stdout.write(self.style.SUCCESS(f'  Created {len(saved_orders)} orders with PKs assigned'))
        self.stdout.write('  M2M can now be set with: order.tags.add(tag)')

        # SOLUTION 2: bulk_create then bulk-create M2M through table entries separately
        self.stdout.write('\n--- Solution 2: bulk_create + explicit M2M through-table inserts ---')
        self.stdout.write('  1. bulk_create the main objects (pass update_conflicts=False)')
        self.stdout.write('  2. Re-query to get PKs: orders = Order.objects.filter(...)')
        self.stdout.write('  3. Bulk-insert through-table rows: ThroughModel.objects.bulk_create(rows)')
        self.stdout.write(self.style.SUCCESS('  This is the high-performance approach for large imports'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - M2M relations require a saved PK on both sides before linking')
        self.stdout.write('  - Use save() or post-query PK assignment before any .add()/.set() calls')
        self.stdout.write('  - For bulk imports, build the through-table rows manually and bulk_create them')
