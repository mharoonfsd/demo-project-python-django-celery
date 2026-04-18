from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q25 SOLUTION: Wrap Celery task dispatch (or any side-effecting code) inside
    transaction.on_commit(). This defers the call until AFTER the current
    transaction has been committed, guaranteeing the row is visible to all DB
    connections — including the Celery worker process.
    """
    help = 'Q25 Solution: Use transaction.on_commit() to defer task dispatch'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q25 SOLUTION: transaction.on_commit() defers dispatch until commit')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        dispatch_log = []

        def safe_task_dispatch(sender, instance, created, **kwargs):
            """
            Wraps task dispatch in on_commit — fires only after the transaction commits.
            The Celery worker will always find the row in the DB.
            """
            if not created:
                return
            pk = instance.pk

            def dispatch():
                dispatch_log.append(f'Task dispatched for pk={pk} (after commit)')
                self.stdout.write(f'  [on_commit] Dispatching task for pk={pk} — row now committed')
                # In production: send_confirmation_email.delay(pk)
                try:
                    fetched = Order.objects.get(pk=pk)
                    self.stdout.write(self.style.SUCCESS(
                        f'  [Worker] Found order: {fetched.order_number}  (OK)'
                    ))
                except Order.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'  [Worker] DoesNotExist for pk={pk}'))

            transaction.on_commit(dispatch)
            self.stdout.write(f'  [Signal] Registered on_commit callback for pk={pk} (not fired yet)')

        post_save.connect(safe_task_dispatch, sender=Order, weak=False)

        self.stdout.write('Opening transaction and creating order...')
        with transaction.atomic():
            order = Order.objects.create(
                order_number='Q25-SOL-ORDER-1',
                customer_email='q25sol@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )
            self.stdout.write(f'Order created inside transaction (pk={order.pk})')
            self.stdout.write('Task NOT yet dispatched — waiting for commit...')

        # on_commit callbacks have now run (we are outside the atomic block)
        self.stdout.write(f'\nTransaction committed. Dispatch log: {dispatch_log}')
        self.stdout.write(self.style.SUCCESS('\nNo DoesNotExist — row was committed before task ran.'))

        post_save.disconnect(safe_task_dispatch, sender=Order)

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always wrap Celery .delay()/.apply_async() in transaction.on_commit()')
        self.stdout.write('  - on_commit callbacks run after the outermost atomic() commits')
        self.stdout.write('  - During tests, use TestCase (not TransactionTestCase) to capture on_commit')
        self.stdout.write('  - Use django-test-migrations or mute_signals() to test signal-driven tasks')
