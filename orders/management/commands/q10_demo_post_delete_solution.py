import logging
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete

from orders.models import Order, Tax

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Q10 SOLUTION: Always log in post_delete handlers.
    Catch exceptions, emit a structured log with the error, and optionally
    re-raise or queue a retry. At minimum, failures must be observable.
    """
    help = 'Q10 Solution: Add logging and proper error handling to post_delete'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q10 SOLUTION: Observable post_delete with logging')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        order = Order.objects.create(
            order_number='Q10-SOL-ORDER-1',
            customer_email='q10sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created: pk={order.pk}')

        # SOLUTION: log every meaningful event; never silently swallow exceptions
        def safe_post_delete(sender, instance, **kwargs):
            self.stdout.write(f'  [AUDIT] Order {instance.pk} ({instance.order_number}) deleted.')
            logger.info('Order deleted: pk=%s order_number=%s', instance.pk, instance.order_number)
            try:
                # Simulate notifying an external system
                raise ConnectionError('Could not notify external system')
            except Exception as e:
                # Log the failure — it is now observable and traceable
                logger.error(
                    'post_delete handler failed for Order %s: %s',
                    instance.pk, e
                )
                self.stdout.write(self.style.WARNING(
                    f'  [WARN] Notification failed (logged, not swallowed): {e}'
                ))
                # Optionally: queue a retry task here

        post_delete.connect(safe_post_delete, sender=Order, dispatch_uid='q10_safe')

        self.stdout.write('\nDeleting order...')
        order.delete()

        post_delete.disconnect(safe_post_delete, sender=Order, dispatch_uid='q10_safe')

        self.stdout.write(self.style.SUCCESS('\nDeletion handled with full observability.'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always emit a structured log on delete (audit trail)')
        self.stdout.write('  - Catch exceptions and log them — never use bare except + pass')
        self.stdout.write('  - Consider queuing a Celery retry for transient external failures')
