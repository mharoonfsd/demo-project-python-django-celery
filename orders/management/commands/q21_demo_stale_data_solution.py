from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q21 SOLUTION: Call instance.refresh_from_db() to reload fields from the
    database before using potentially stale data. Optionally, pass fields=[]
    to refresh only specific columns.
    """
    help = 'Q21 Solution: Use refresh_from_db() to reload stale instances'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q21 SOLUTION: refresh_from_db() reloads current data')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q21-SOL-ORDER-1',
            customer_email='q21sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Loaded order pk={order.pk}, amount={order.amount}')

        # Simulate another process updating the row
        Order.objects.filter(pk=order.pk).update(amount=Decimal('999.00'))
        self.stdout.write('\nAnother process updated amount to 999.00 in the DB')
        self.stdout.write(f'Before refresh: order.amount = {order.amount}  (stale)')

        # SOLUTION: refresh before using the value
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'After refresh_from_db(): order.amount = {order.amount}  (correct!)'
        ))

        # You can also refresh only specific fields for efficiency
        Order.objects.filter(pk=order.pk).update(price=Decimal('888.00'))
        order.refresh_from_db(fields=['price'])
        self.stdout.write(f'After targeted refresh (fields=["price"]): order.price = {order.price}')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Call refresh_from_db() before reading fields that could have been updated')
        self.stdout.write('  - Use fields=["col1", "col2"] to refresh only the columns you need')
        self.stdout.write('  - After a long-running process, always refresh before continuing')
        self.stdout.write('  - Consider re-querying with .get(pk=...) to get a fresh instance')
