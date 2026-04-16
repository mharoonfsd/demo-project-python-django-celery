from django.core.management.base import BaseCommand
from orders.models import Order


class Command(BaseCommand):
    help = 'Demonstrate bulk_create signal issue'

    def handle(self, *args, **options):
        self.stdout.write('Creating orders with bulk_create...')

        orders_list = [
            Order(order_number=f'ORDER-{i}', customer_email=f'customer{i}@example.com', amount=100.00)
            for i in range(1, 6)
        ]

        # This will NOT trigger post_save signals
        Order.objects.bulk_create(orders_list)

        self.stdout.write(self.style.SUCCESS(f'Created {len(orders_list)} orders with bulk_create'))
        self.stdout.write('Notice: No notification emails were sent (signals not triggered)')

        # Now create one with regular save
        self.stdout.write('\nCreating one order with regular save...')
        order = Order.objects.create(
            order_number='ORDER-REGULAR',
            customer_email='regular@example.com',
            amount=200.00
        )
        self.stdout.write(self.style.SUCCESS('Created order with regular save'))
        self.stdout.write('Notice: Notification email was sent (signal triggered)')