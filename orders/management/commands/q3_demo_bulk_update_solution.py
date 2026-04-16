from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from orders.models import Order


class Command(BaseCommand):
    help = 'Demonstrate the SOLUTION: Manually trigger logic after bulk_update'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()

        self.stdout.write('Creating orders with regular save...')
        orders = []
        for i in range(1, 4):
            order = Order(
                order_number=f'ORDER-BULK-SOL-{i}',
                customer_email=f'bulk{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            order._skip_notification = True  # Skip initial notification
            order.save()
            orders.append(order)
            self.stdout.write(self.style.SUCCESS(f'Created order {order.order_number}'))

        self.stdout.write('\nSOLUTION: bulk_update + manual signal triggering...')
        # Update prices using bulk_update
        for order in orders:
            order.price = Decimal('150.00')

        Order.objects.bulk_update(orders, ['price'])

        self.stdout.write(self.style.SUCCESS('Updated orders with bulk_update'))

        # SOLUTION: Manually trigger post_save signals for critical logic
        self.stdout.write('\nManually triggering post_save signals...')
        for order in orders:
            # Simulate what the signal would do - send notification for the update
            self.stdout.write(f'Sending notification for updated order {order.order_number}')
            # In real code: send email or trigger business logic here

        self.stdout.write('\nAlternative SOLUTION: Use individual saves for critical updates...')
        # For truly critical updates, use regular save() instead of bulk_update
        order = Order.objects.get(order_number='ORDER-BULK-SOL-1')
        order.price = Decimal('200.00')
        order.save()  # This properly triggers all signals
        self.stdout.write(self.style.SUCCESS(f'Updated order with save() - signals triggered'))

        self.stdout.write('\nSOLUTION benefits:')
        self.stdout.write(' - Manual triggering ensures critical logic runs')
        self.stdout.write(' - Alternative: Use save() for operations requiring signals')
        self.stdout.write(' - Clear understanding of when signals are bypassed')
        self.stdout.write(' - Prevents silent failures in production')