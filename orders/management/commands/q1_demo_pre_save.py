from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    help = 'Demonstrate the PROBLEM: pre_save race conditions from non-atomic read-modify-write'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()
        Tax.objects.all().delete()

        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write(self.style.SUCCESS(f'Created Tax(name={tax.name}, value={tax.value})'))

        order = Order(
            order_number='ORDER-PRE-SAVE-PROBLEM',
            customer_email='race-demo@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order._skip_notification = True
        order.save()  # This triggers the unsafe pre_save calculation
        self.stdout.write(self.style.SUCCESS(
            f'Created order {order.order_number} price={order.price} total={order.total}'
        ))

        self.stdout.write('\nPROBLEM demonstration:')
        self.stdout.write(' - pre_save signal computes total = price + Tax.value')
        self.stdout.write(' - This is a read-modify-write operation that is NOT atomic')
        self.stdout.write(' - Under heavy load, multiple threads can read stale Tax.value')
        self.stdout.write(' - They compute different totals and overwrite each other')

        self.stdout.write('\nSimulating concurrent update (problematic):')
        order.price = Decimal('110.00')
        order.save()  # pre_save recalculates total unsafely
        self.stdout.write(self.style.WARNING(
            f'After unsafe save(), order total = {order.total} (may be inconsistent)'
        ))

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write(' - If Tax.value changes between read and write, total becomes wrong')
        self.stdout.write(' - Race conditions cause data corruption in production')
        self.stdout.write(' - No atomicity across the Tax lookup and Order update')
