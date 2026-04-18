from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q23 SOLUTION: Break the recursion with one of three patterns:
      1. Guard flag: set a flag on the instance before calling save(), check
         the flag at the top of the handler and return early if set.
      2. update_fields: use save(update_fields=[...]) so the signal fires but
         the handler can check kwargs['update_fields'] and skip re-processing.
      3. update() bypass: use QuerySet.update() (no signals at all) for the
         internal modification — only appropriate when signals are intentionally skipped.
    """
    help = 'Q23 Solution: Break signal recursion with guard flag or update_fields'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q23 SOLUTION: Break recursive signals')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        call_count = [0]

        # SOLUTION 1: Guard flag on instance
        def safe_signal_handler(sender, instance, created, **kwargs):
            """Use a flag to prevent re-entry."""
            if getattr(instance, '_in_signal', False):
                return  # Prevent recursion
            call_count[0] += 1
            self.stdout.write(f'  Signal handler called once (count={call_count[0]})')
            instance._in_signal = True         # set guard
            instance.amount += Decimal('1.00')
            instance.save()                    # safe — handler returns early above
            instance._in_signal = False        # clear guard

        post_save.connect(safe_signal_handler, sender=Order, weak=False)

        self.stdout.write('--- Solution 1: Guard flag (_in_signal) ---')
        order = Order.objects.create(
            order_number='Q23-SOL-ORDER-1',
            customer_email='q23sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created successfully. Signal called {call_count[0]} time(s). '
            f'Final amount: {order.amount}'
        ))
        post_save.disconnect(safe_signal_handler, sender=Order)

        # SOLUTION 2: update_fields sentinel
        self.stdout.write('\n--- Solution 2: update_fields sentinel ---')
        call_count[0] = 0

        def updatefields_signal_handler(sender, instance, created, **kwargs):
            """Skip handler if we're already doing a signal-triggered save."""
            update_fields = kwargs.get('update_fields') or ()
            if 'amount' in update_fields:
                # This save was triggered by the handler itself — skip
                return
            call_count[0] += 1
            self.stdout.write(f'  Business save detected, applying update (count={call_count[0]})')
            instance.amount += Decimal('1.00')
            instance.save(update_fields=['amount'])  # sentinel field list

        post_save.connect(updatefields_signal_handler, sender=Order, weak=False)
        order2 = Order.objects.create(
            order_number='Q23-SOL-ORDER-2',
            customer_email='q23sol2@example.com',
            amount=Decimal('200.00'),
            price=Decimal('200.00'),
        )
        order2.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'Created successfully. Signal called {call_count[0]} time(s). '
            f'Final amount: {order2.amount}'
        ))
        post_save.disconnect(updatefields_signal_handler, sender=Order)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use _in_signal instance flag to guard against re-entry')
        self.stdout.write('  - Use save(update_fields=[...]) as a sentinel to differentiate saves')
        self.stdout.write('  - Consider moving the logic out of signals entirely (Q24 pattern)')
