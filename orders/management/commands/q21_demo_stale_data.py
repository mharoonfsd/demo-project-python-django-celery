from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q21 PROBLEM: Once a Django model instance is loaded into memory, it is NOT
    automatically refreshed when another process or query updates the same row.
    Reading fields from a stale instance silently returns outdated data.
    """
    help = 'Q21 Problem: Stale in-memory instance returns outdated field values'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q21 PROBLEM: Stale instance — missing refresh_from_db()')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q21-ORDER-1',
            customer_email='q21@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Loaded order pk={order.pk}, amount={order.amount}')

        # Another process / query updates the row directly
        Order.objects.filter(pk=order.pk).update(amount=Decimal('999.00'))
        self.stdout.write('\nAnother process updated amount to 999.00 in the DB')

        # PROBLEM: our in-memory instance still shows the old value
        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: order.amount is still {order.amount} (stale!)'
        ))
        self.stdout.write('  Reading order.amount without refresh returns the original value.')
        self.stdout.write('  Any business logic using this value will produce wrong results.')
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Silent bug: no exception raised')
        self.stdout.write('  - Calculations (totals, discounts) are based on wrong data')
        self.stdout.write('  - Overwriting with .save() will revert the other process\'s update')
