from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q7 PROBLEM: QuerySet.update() issues raw SQL and bypasses:
      - model.save() override logic
      - pre_save / post_save signals
      - full_clean() / model validation
    This means business logic in save() or signals is silently skipped.
    """
    help = 'Q7 Problem: update() skips signals and model.save() logic'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q7 PROBLEM: update() bypasses save() and signals')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        signal_fired = []

        def track_signal(sender, instance, **kwargs):
            signal_fired.append(instance.pk)

        post_save.connect(track_signal, sender=Order, dispatch_uid='q7_track')

        order = Order.objects.create(
            order_number='Q7-ORDER-1',
            customer_email='q7@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created (pk={order.pk}). Signal fired for pks: {signal_fired}')
        signal_fired.clear()

        # PROBLEM: update() does NOT fire post_save signal
        self.stdout.write('\nCalling update() on queryset...')
        Order.objects.filter(pk=order.pk).update(amount=Decimal('999.00'))

        post_save.disconnect(track_signal, sender=Order, dispatch_uid='q7_track')

        self.stdout.write(self.style.ERROR(
            f'Signal fired for pks after update(): {signal_fired}  (EMPTY — signal was NOT triggered)'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Business logic in post_save (notifications, audit logs) is silently skipped')
        self.stdout.write('  - model.save() override (e.g. total recalculation) is also bypassed')
        self.stdout.write('  - No exception is raised — bugs are invisible')
