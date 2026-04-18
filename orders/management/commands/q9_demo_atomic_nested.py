from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q9 PROBLEM: When an inner atomic() block raises an exception, Django
    marks the entire transaction as needing rollback. Any subsequent DB
    operation inside the outer atomic() block raises TransactionManagementError
    ("An error occurred in the current transaction. You can't execute queries
    until the end of the 'atomic' block"), even if the developer caught the
    inner exception and intended to continue.
    """
    help = 'Q9 Problem: Inner atomic() exception poisons the outer transaction'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q9 PROBLEM: Nested atomic() leaves outer transaction broken')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        try:
            with transaction.atomic():  # outer block
                Order.objects.create(
                    order_number='Q9-ORDER-OUTER',
                    customer_email='q9outer@example.com',
                    amount=Decimal('100.00'),
                    price=Decimal('100.00'),
                )
                self.stdout.write('Outer: created Q9-ORDER-OUTER')

                try:
                    with transaction.atomic():  # inner block — will fail
                        Order.objects.create(
                            order_number='Q9-ORDER-INNER',
                            customer_email='q9inner@example.com',
                            amount=Decimal('50.00'),
                            price=Decimal('50.00'),
                        )
                        raise ValueError('Simulated inner failure')
                except ValueError as e:
                    self.stdout.write(self.style.WARNING(f'Inner exception caught: {e}'))
                    self.stdout.write('  Developer thinks they recovered — but outer TX is now broken!')

                # PROBLEM: This next DB op will raise TransactionManagementError
                self.stdout.write('Trying to create another order in outer block...')
                Order.objects.create(
                    order_number='Q9-ORDER-AFTER',
                    customer_email='q9after@example.com',
                    amount=Decimal('75.00'),
                    price=Decimal('75.00'),
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nOuter transaction failed: {type(e).__name__}: {e}'))

        count = Order.objects.count()
        self.stdout.write(self.style.ERROR(f'\nOrders in DB: {count}  (outer TX rolled back too)'))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Catching an inner exception does NOT restore the outer transaction')
        self.stdout.write('  - All work in the outer block is lost on rollback')
        self.stdout.write('  - TransactionManagementError is confusing and hard to diagnose')
