from django.core.management.base import BaseCommand
from django.db import connection, utils as db_utils
from orders.models import Order, Tax

class Command(BaseCommand):
    help = 'Demonstrate CASCADE not working due to raw SQL or DB mismatch (Problem Demo for Q4)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- Q4 Problem Demo: CASCADE not working ---'))
        # Truncate tables for a clean demo
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM orders_order;')
            cursor.execute('DELETE FROM orders_tax;')
        self.stdout.write('Database truncated.')

        # Create a Tax and an Order referencing it
        tax = Tax.objects.create(name='Standard', value=10)
        order = Order.objects.create(order_number='Q4-ORDER-1', customer_email='q4@example.com', amount=100, price=100, tax=tax)
        self.stdout.write(f'Created Tax: {tax}')
        self.stdout.write(f'Created Order: {order}')

        # Simulate a raw SQL delete (bypassing Django ORM)
        self.stdout.write('\nDeleting Tax using raw SQL (bypassing ORM CASCADE)...')
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM orders_tax WHERE id = %s;', [tax.id])
            self.stdout.write('Tax deleted using raw SQL.')
        except db_utils.IntegrityError as e:
            self.stdout.write(self.style.ERROR(
                f'PROBLEM: Raw SQL deletion blocked by DB FK constraint: {e}\n'
                '  In production DBs without FK enforcement, this deletion WOULD succeed,\n'
                '  leaving orphaned Order rows with a stale tax_id (data corruption).'
            ))
            self.stdout.write('\n--- End of Q4 Problem Demo ---')
            return

        # Check if Order still exists (should be orphaned)
        remaining_orders = Order.objects.all()
        if remaining_orders.exists():
            self.stdout.write(self.style.ERROR('Order still exists! CASCADE did NOT work.'))
        else:
            self.stdout.write(self.style.SUCCESS('Order deleted. CASCADE worked.'))

        self.stdout.write('\n--- End of Q4 Problem Demo ---')
