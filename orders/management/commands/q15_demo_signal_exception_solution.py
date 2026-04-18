from decimal import Decimal
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from orders.models import Order, Tax

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Q15 SOLUTION: Wrap signal handler bodies in try/except so that non-critical
    side effects (email, notifications) cannot abort the main transaction.
    Log the failure so it is observable without crashing the caller.
    """
    help = 'Q15 Solution: Handle signal exceptions gracefully so transaction is not broken'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q15 SOLUTION: Safe signal exception handling')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # SOLUTION: wrap signal body in try/except — isolate side-effects
        def safe_signal(sender, instance, created, **kwargs):
            if created:
                try:
                    # Simulates calling an external API or email service that is down
                    raise RuntimeError('Email service down')
                except Exception as e:
                    # Log and continue — do NOT let non-critical failure abort the transaction
                    logger.error('Signal handler failed (non-fatal): %s', e)
                    print(f'  [SIGNAL] Non-fatal error caught and logged: {e}')

        post_save.connect(safe_signal, sender=Order, dispatch_uid='q15_safe')

        self.stdout.write('Creating Order inside atomic()...')
        try:
            with transaction.atomic():
                order = Order(
                    order_number='Q15-ORDER-SOL',
                    customer_email='q15sol@example.com',
                    amount=Decimal('100.00'),
                    price=Decimal('100.00'),
                )
                order._skip_notification = True
                order.save()   # safe_signal fires; exception is caught internally
                self.stdout.write(f'  Order saved with pk={order.pk}')
        finally:
            post_save.disconnect(safe_signal, sender=Order, dispatch_uid='q15_safe')

        count = Order.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\nOrders in DB: {count}'))
        self.stdout.write(self.style.SUCCESS(
            'SOLUTION: Order was saved successfully even though the signal handler failed.'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always wrap side-effects (email, HTTP calls) in try/except inside signals')
        self.stdout.write('  - Log failures so they are observable without crashing the caller')
        self.stdout.write('  - Consider moving side-effects to Celery tasks with their own retry logic')
