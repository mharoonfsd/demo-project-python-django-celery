from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q10 PROBLEM: A post_delete signal fires after an object is deleted.
    If the handler has no logging and silently raises or does nothing
    observable, deletions become untraceable — "silent failure".
    Audit trails are missing and debugging is impossible.
    """
    help = 'Q10 Problem: post_delete with no logging causes silent, untraceable failures'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q10 PROBLEM: post_delete silent failure (no logging)')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q10-ORDER-1',
            customer_email='q10@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created: pk={order.pk}')

        # PROBLEM: signal handler with silent pass on error and no logging
        def broken_post_delete(sender, instance, **kwargs):
            try:
                # Simulate an external cleanup call that fails
                raise ConnectionError('Could not notify external system')
            except Exception:
                pass  # Silent! No log, no re-raise, no metric — failure is invisible

        post_delete.connect(broken_post_delete, sender=Order, dispatch_uid='q10_broken')

        self.stdout.write('\nDeleting order...')
        order.delete()

        post_delete.disconnect(broken_post_delete, sender=Order, dispatch_uid='q10_broken')

        self.stdout.write(self.style.ERROR(
            'PROBLEM: Order deleted but post_delete handler silently failed.'
        ))
        self.stdout.write('  - External system was NOT notified')
        self.stdout.write('  - No log entry, no metric, no alert — completely invisible')
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Stale data in external systems')
        self.stdout.write('  - No audit trail for compliance or debugging')
        self.stdout.write('  - Bare except + pass is an anti-pattern')
