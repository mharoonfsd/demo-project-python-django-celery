from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    help = 'Demonstrate the PROBLEM: save() override and signals execution order'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()
        Tax.objects.all().delete()

        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write(self.style.SUCCESS(f'Created Tax(name={tax.name}, value={tax.value})'))

        # Create order with custom save() that sets total
        order = Order(
            order_number='ORDER-SAVE-SIGNALS-PROBLEM',
            customer_email='order-demo@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order._custom_total = Decimal('150.00')  # Custom value to set in save()
        order.save()  # This will trigger save() override and then signals
        self.stdout.write(self.style.SUCCESS(
            f'Created order {order.order_number} price={order.price} total={order.total}'
        ))

        self.stdout.write('\nPROBLEM demonstration:')
        self.stdout.write(' - save() override runs first and sets total to custom value')
        self.stdout.write(' - Then pre_save signal runs and overwrites total with price + tax')
        self.stdout.write(' - Final total is from signal, not from save() override')

        self.stdout.write('\nExecution order:')
        self.stdout.write(' 1. save() method executes (sets total=150.00)')
        self.stdout.write(' 2. DB write happens')
        self.stdout.write(' 3. pre_save signal executes (overwrites total=105.00)')

        self.stdout.write('\nWhy this is problematic:')
        self.stdout.write(' - Signals run after save(), potentially overwriting changes')
        self.stdout.write(' - Business logic split between save() and signals is confusing')
        self.stdout.write(' - Can lead to unexpected overwrites and bugs')