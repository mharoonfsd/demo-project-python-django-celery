from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q15 PROBLEM: An unhandled exception inside a signal handler bubbles up
    and rolls back the entire enclosing transaction — even if the DB write
    itself succeeded. The developer may not expect a notification failure
    to abort the whole save.
    """
    help = 'Q15 Problem: Unhandled signal exception rolls back the transaction'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q15 PROBLEM: Signal exception breaks transaction')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Connect a deliberately broken signal for this demo only
        def broken_signal(sender, instance, created, **kwargs):
            if created:
                # Simulates calling an external API or email service that is down
                raise RuntimeError('Signal handler crashed! (e.g. email service down)')

        post_save.connect(broken_signal, sender=Order, dispatch_uid='q15_broken')

        self.stdout.write('Attempting to create an Order inside atomic()...')
        try:
            with transaction.atomic():
                order = Order(
                    order_number='Q15-ORDER-1',
                    customer_email='q15@example.com',
                    amount=Decimal('100.00'),
                    price=Decimal('100.00'),
                )
                order._skip_notification = True   # suppress default signal
                order.save()                       # broken_signal fires here
                self.stdout.write(f'  Order saved with pk={order.pk}')
        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(f'\nRuntimeError caught: {e}'))
        finally:
            post_save.disconnect(broken_signal, sender=Order, dispatch_uid='q15_broken')

        count = Order.objects.count()
        self.stdout.write(self.style.WARNING(f'\nOrders in DB after error: {count}'))
        self.stdout.write(self.style.ERROR(
            'PROBLEM: The Order was NOT saved — signal exception rolled back the transaction.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - A notification failure causes data loss')
        self.stdout.write('  - Non-critical side-effects abort critical data writes')
        self.stdout.write('  - Hard to debug because the error originates inside the signal')
