from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import F

from orders.models import Order, Tax


class Command(BaseCommand):
    help = 'Demonstrate pre_save race conditions and the DB-level atomic update fix'

    def handle(self, *args, **options):
        self.stdout.write('Resetting demo state...')
        Order.objects.all().delete()
        Tax.objects.all().delete()

        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write(self.style.SUCCESS(f'Created Tax(name={tax.name}, value={tax.value})'))

        order = Order(
            order_number='ORDER-PRE-SAVE',
            customer_email='race-demo@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        order._skip_notification = True
        order.save()
        self.stdout.write(self.style.SUCCESS(
            f'Created order {order.order_number} price={order.price} total={order.total}'
        ))

        self.stdout.write('\nProblem demonstration:')
        self.stdout.write(' - pre_save computes total from a separate Tax lookup')
        self.stdout.write(' - the logic is not atomic across reads and writes')
        self.stdout.write(' - under concurrent updates, a stale lookup can overwrite a newer total')

        self.stdout.write('\nNaive save() path:')
        order.price = Decimal('110.00')
        order.save()
        self.stdout.write(self.style.SUCCESS(
            f'After save(), order total = {order.total} (calculated by pre_save)'
        ))

        self.stdout.write('\nAtomic fix: use DB-level update with F()')
        Order.objects.filter(id=order.id).update(total=F('price') + Decimal('5.00'))
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'After atomic update, order total = {order.total}'
        ))

        self.stdout.write('\nFix rationale:')
        self.stdout.write(' - avoid modifying derived fields inside save/pre_save when the value depends on another lookup')
        self.stdout.write(' - use direct update(...) with F() to keep the operation atomic at the DB level')
        self.stdout.write(' - this prevents race conditions from non-atomic read-modify-write.')
