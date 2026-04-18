from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q25 PROBLEM: A post_save signal dispatches a Celery task (or runs code)
    BEFORE the transaction that triggered the save has been committed to the DB.

    When the Celery worker immediately picks up the task and queries the DB,
    the row doesn't exist yet — it's still in an uncommitted transaction.
    Result: DoesNotExist error in the worker, or operating on a phantom row.
    """
    help = 'Q25 Problem: Signal dispatches task before transaction commits — row not found'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q25 PROBLEM: Signal fires before transaction commits')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        task_fired_order_ids = []
        task_found_order = []

        def premature_task_dispatch(sender, instance, created, **kwargs):
            """
            Fires inside the OPEN transaction — before commit.
            A Celery worker querying the DB right now sees no row yet.
            """
            if not created:
                return
            task_fired_order_ids.append(instance.pk)
            self.stdout.write(f'  [Signal] Dispatching task for pk={instance.pk} (TX still open!)')
            # Simulate: Celery worker immediately tries to fetch the row
            try:
                fetched = Order.objects.get(pk=instance.pk)
                task_found_order.append(fetched)
                self.stdout.write(f'  [Worker] Found order: {fetched.order_number}')
            except Order.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'  [Worker] DoesNotExist for pk={instance.pk} — row not yet committed!'
                ))

        post_save.connect(premature_task_dispatch, sender=Order, weak=False)

        self.stdout.write('Opening explicit transaction and creating order...')
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_number='Q25-ORDER-1',
                    customer_email='q25@example.com',
                    amount=Decimal('100.00'),
                    price=Decimal('100.00'),
                )
                self.stdout.write(f'Order created inside transaction (pk={order.pk})')
                self.stdout.write('(Transaction is still OPEN — not committed yet)')
                # post_save fires here, inside the atomic block
        finally:
            post_save.disconnect(premature_task_dispatch, sender=Order)

        self.stdout.write(self.style.WARNING(
            f'\nNote: In production the Celery worker runs in a separate process '
            f'and almost always hits DoesNotExist when dispatched from inside a transaction.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Celery task runs before DB row is visible to other connections')
        self.stdout.write('  - Causes random DoesNotExist errors that are hard to reproduce')
        self.stdout.write('  - The task retry logic masks the root cause')
