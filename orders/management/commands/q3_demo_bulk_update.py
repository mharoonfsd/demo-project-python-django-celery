from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order


class Command(BaseCommand):
    help = 'Demonstrate the PROBLEM: bulk_update() does not trigger signals'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()

        self.stdout.write('Creating orders with regular save (triggers signals)...')
        orders = []
        for i in range(1, 4):
            order = Order(
                order_number=f'ORDER-BULK-{i}',
                customer_email=f'bulk{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            order.save()  # This triggers post_save signal
            orders.append(order)
            self.stdout.write(self.style.SUCCESS(f'Created order {order.order_number}'))

        self.stdout.write('\nNow updating orders with bulk_update (bypasses signals)...')
        # Update prices using bulk_update - this will NOT trigger signals
        for order in orders:
            order.price = Decimal('150.00')

        Order.objects.bulk_update(orders, ['price'])

        self.stdout.write(self.style.WARNING('Updated orders with bulk_update'))
        self.stdout.write('Notice: No notification emails were sent (signals not triggered)')

        # Refresh from DB to see changes
        orders = Order.objects.filter(order_number__startswith='ORDER-BULK-')
        for order in orders:
            self.stdout.write(f'Order {order.order_number}: price={order.price}')

        self.stdout.write('\nPROBLEM demonstration:')
        self.stdout.write(' - bulk_update() executes direct SQL, bypassing ORM lifecycle')
        self.stdout.write(' - Signals (post_save, pre_save) are never called')
        self.stdout.write(' - Business logic in signals is silently skipped')
        self.stdout.write(' - No notifications, validations, or side effects occur')

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write(' - Critical business logic may be missed')
        self.stdout.write(' - Data integrity issues if signals handle important updates')
        self.stdout.write(' - Silent failures - no errors, just missing behavior')