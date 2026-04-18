from decimal import Decimal
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q14 SOLUTION: Always use model.save() (or update specific fields with
    update_fields) when you need auto_now=True fields to be kept current.

    Best practice: If you need bulk performance but still want timestamps,
    manually set the field value before calling update() or bulk_update().
    """
    help = 'Q14 Solution: Use save() or manually set timestamps when using update()'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q14 SOLUTION: Keeping auto_now fields accurate')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q14-ORDER-SOL',
            customer_email='q14sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created at: {order.created_at}')

        time.sleep(1)

        # SOLUTION 1: Use save(update_fields=[...]) — auto_now fields ARE updated
        self.stdout.write('\n--- Solution 1: Use save(update_fields=[...]) ---')
        order.amount = Decimal('200.00')
        order.save(update_fields=['amount'])
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'After save(update_fields=["amount"]) — amount={order.amount}'
        ))
        self.stdout.write('  auto_now fields would be updated correctly by ORM.')

        # SOLUTION 2: If you must use update(), explicitly pass the timestamp
        self.stdout.write('\n--- Solution 2: Pass timestamp explicitly in update() ---')
        Order.objects.filter(pk=order.pk).update(
            amount=Decimal('300.00'),
            # In a model with updated_at: updated_at=timezone.now()
        )
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'After explicit update() — amount={order.amount}'
        ))
        self.stdout.write('  Best practice: always pass updated_at=timezone.now() in bulk update() calls.')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - save() / save(update_fields=[...]) always triggers auto_now')
        self.stdout.write('  - update() requires you to manually manage timestamp fields')
        self.stdout.write('  - Prefer save(update_fields=[...]) for selective saves with timestamp accuracy')
