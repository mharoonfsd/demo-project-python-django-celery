from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    help = 'Demonstrate the SOLUTION: Consolidate logic in save() to avoid signal overwrites'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()
        Tax.objects.all().delete()

        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write(self.style.SUCCESS(f'Created Tax(name={tax.name}, value={tax.value})'))

        # Create order with save() handling total calculation
        order = Order(
            order_number='ORDER-SAVE-SIGNALS-SOLUTION',
            customer_email='order-demo@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order._use_safe_calculation = True  # Flag to use save() logic instead of signal
        order.save()  # save() calculates total, signals are skipped
        self.stdout.write(self.style.SUCCESS(
            f'Created order {order.order_number} price={order.price} total={order.total}'
        ))

        self.stdout.write('\nSOLUTION demonstration:')
        self.stdout.write(' - All business logic consolidated in save() method')
        self.stdout.write(' - Signals are disabled for this operation')
        self.stdout.write(' - No risk of signals overwriting save() changes')

        self.stdout.write('\nExecution order:')
        self.stdout.write(' 1. save() method executes and calculates total')
        self.stdout.write(' 2. DB write happens with correct total')
        self.stdout.write(' 3. No signals run to overwrite the value')

        self.stdout.write('\nWhy this works:')
        self.stdout.write(' - Single source of truth for business logic')
        self.stdout.write(' - No hidden side effects from signals')
        self.stdout.write(' - Predictable behavior and easier debugging')