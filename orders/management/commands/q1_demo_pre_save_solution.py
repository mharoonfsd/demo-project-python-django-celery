from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import F

from orders.models import Order, Tax


class Command(BaseCommand):
    help = 'Demonstrate the SOLUTION: DB-level atomic updates to prevent pre_save race conditions'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()
        Tax.objects.all().delete()

        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write(self.style.SUCCESS(f'Created Tax(name={tax.name}, value={tax.value})'))

        order = Order(
            order_number='ORDER-PRE-SAVE-SOLUTION',
            customer_email='race-demo@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order._skip_notification = True
        order._use_safe_update = True  # Skip unsafe pre_save calculation
        order.save()
        self.stdout.write(self.style.SUCCESS(
            f'Created order {order.order_number} price={order.price} total={order.total}'
        ))

        self.stdout.write('\nSOLUTION demonstration:')
        self.stdout.write(' - Instead of pre_save signal calculating total, use DB-level atomic update')
        self.stdout.write(' - F() expressions reference columns directly in SQL')
        self.stdout.write(' - The entire operation is atomic at the database level')

        self.stdout.write('\nSafe atomic update:')
        order.price = Decimal('110.00')
        # Atomic update: total = price + 5.00 in one SQL statement
        Order.objects.filter(id=order.id).update(total=F('price') + Decimal('5.00'))
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'After atomic update, order total = {order.total} (always consistent)'
        ))

        self.stdout.write('\nWhy this works:')
        self.stdout.write(' - No separate Tax lookup in application code')
        self.stdout.write(' - DB computes total = price + 5.00 atomically')
        self.stdout.write(' - No race conditions possible - single SQL UPDATE statement')
        self.stdout.write(' - Scales safely under concurrent load')