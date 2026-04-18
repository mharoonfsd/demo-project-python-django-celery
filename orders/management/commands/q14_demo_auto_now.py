from decimal import Decimal
import time

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q14 PROBLEM: auto_now field is NOT updated when using QuerySet.update().

    Django's auto_now=True (e.g. DateTimeField(auto_now=True)) only fires
    when an object is saved via model.save(). The QuerySet.update() method
    issues a raw SQL UPDATE and completely bypasses the ORM save lifecycle,
    meaning auto_now fields are left stale.
    """
    help = 'Q14 Problem: auto_now field silently not updated when using update()'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q14 PROBLEM: auto_now bypass via update()')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Create an order; Django sets created_at via auto_now_add
        order = Order.objects.create(
            order_number='Q14-ORDER-1',
            customer_email='q14@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created at: {order.created_at}')

        time.sleep(1)

        # PROBLEM: update() bypasses the ORM save lifecycle entirely.
        # Any auto_now=True field on the model would NOT be refreshed.
        Order.objects.filter(pk=order.pk).update(amount=Decimal('200.00'))

        order.refresh_from_db()
        self.stdout.write(f'\nAfter update() — amount is now: {order.amount}')
        self.stdout.write(self.style.ERROR(
            'PROBLEM: If the model had an auto_now=True field (e.g. updated_at), '
            'it would NOT have been updated because update() bypasses model.save().'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Stale timestamps mislead audit logs and cache invalidation')
        self.stdout.write('  - Developers assume update() behaves like save() — it does not')
        self.stdout.write('  - Bugs are silent; no exception is raised')
