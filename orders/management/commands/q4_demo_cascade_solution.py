from django.core.management.base import BaseCommand
from django.db import connection, transaction
from orders.models import Order, Tax

class Command(BaseCommand):
    help = 'Demonstrate proper CASCADE using Django ORM and DB constraints (Solution Demo for Q4)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Q4 Solution Demo: Proper CASCADE with ORM and DB constraints ---'))
        # Truncate tables for a clean demo
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM orders_order;')
            cursor.execute('DELETE FROM orders_tax;')
        self.stdout.write('Database truncated.')

        # Create a Tax and an Order referencing it
        tax = Tax.objects.create(name='Standard', value=10)
        order = Order.objects.create(order_number='Q4-ORDER-2', customer_email='q4solution@example.com', amount=100, price=100, tax=tax)
        self.stdout.write(f'Created Tax: {tax}')
        self.stdout.write(f'Created Order: {order}')

        # Demonstrate proper CASCADE: delete Tax using ORM
        self.stdout.write('\nDeleting Tax using Django ORM (respects CASCADE)...')
        tax.delete()
        self.stdout.write('Tax deleted using ORM.')

        # Check if Order still exists
        remaining_orders = Order.objects.all()
        if remaining_orders.exists():
            self.stdout.write(self.style.ERROR('Order still exists! CASCADE did NOT work.'))
        else:
            self.stdout.write(self.style.SUCCESS('Order deleted. CASCADE worked as expected.'))

        self.stdout.write('\n--- End of Q4 Solution Demo ---')
