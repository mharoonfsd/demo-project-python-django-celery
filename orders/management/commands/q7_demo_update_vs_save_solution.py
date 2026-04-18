from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q7 SOLUTION: Use model.save() (or save(update_fields=[...])) to ensure
    all signals, model validations, and save() overrides are executed.
    Only use update() for bulk performance-critical operations where you
    consciously accept that signals/validation will be skipped.
    """
    help = 'Q7 Solution: Use save() to trigger signals and model.save() logic'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q7 SOLUTION: save() triggers signals and model logic')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        signal_fired = []

        def track_signal(sender, instance, **kwargs):
            signal_fired.append(instance.pk)

        post_save.connect(track_signal, sender=Order, dispatch_uid='q7_track_sol')

        order = Order.objects.create(
            order_number='Q7-SOL-ORDER-1',
            customer_email='q7sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created (pk={order.pk})')
        signal_fired.clear()

        # SOLUTION: fetch and save() — triggers all signals and model logic
        self.stdout.write('\nCalling save(update_fields=["amount"]) on model instance...')
        order.amount = Decimal('999.00')
        order.save(update_fields=['amount'])  # issues only one UPDATE but goes through ORM

        post_save.disconnect(track_signal, sender=Order, dispatch_uid='q7_track_sol')

        self.stdout.write(self.style.SUCCESS(
            f'Signal fired for pks after save(): {signal_fired}  (signal WAS triggered)'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - save(update_fields=[...]) updates only specific columns but triggers ORM lifecycle')
        self.stdout.write('  - Use update() only for bulk ops where signal bypass is intentional and safe')
        self.stdout.write('  - If using update() for performance, replicate business logic manually')
