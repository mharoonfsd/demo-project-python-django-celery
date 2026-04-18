from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q23 PROBLEM: A signal handler that calls save() on the same model triggers
    the same signal again, creating an infinite recursive loop that ends with
    a RecursionError (Python stack overflow).
    """
    help = 'Q23 Problem: Recursive signal causes infinite loop / RecursionError'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q23 PROBLEM: Recursive signal causes infinite loop')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        call_count = [0]

        def recursive_signal_handler(sender, instance, created, **kwargs):
            """This handler modifies and re-saves the instance, triggering itself again."""
            call_count[0] += 1
            if call_count[0] > 5:
                # Guard to prevent actual stack overflow in the demo
                self.stdout.write(self.style.ERROR(
                    f'  Signal fired {call_count[0]} times! Stopping demo guard at 5.'
                ))
                raise RecursionError(
                    f'Maximum recursion depth exceeded — signal called itself {call_count[0]} times'
                )
            self.stdout.write(f'  Signal handler called (count={call_count[0]})')
            # BUG: Calling save() fires post_save again — infinite loop!
            instance.amount += Decimal('1.00')
            instance.save()  # <-- triggers this handler again!

        post_save.connect(recursive_signal_handler, sender=Order, weak=False)
        try:
            self.stdout.write('Creating order (will trigger recursive signal)...')
            Order.objects.create(
                order_number='Q23-ORDER-1',
                customer_email='q23@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
        except RecursionError as e:
            self.stdout.write(self.style.ERROR(f'\nRecursionError: {e}'))
        finally:
            post_save.disconnect(recursive_signal_handler, sender=Order)

        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Kills the process with RecursionError (unrecoverable 500 error)')
        self.stdout.write('  - Very easy to introduce accidentally when adding "small" signal logic')
        self.stdout.write('  - Hard to debug because the stack trace shows only the signal machinery')
