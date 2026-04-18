from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q41 PROBLEM: If a task's exception handling is misconfigured, successful
    tasks can be retried. For example, retrying on Exception (which includes
    successful runs if return value is checked) or always re-queueing tasks.
    """
    help = 'Q41 Problem: Successful tasks retried due to misconfiguration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q41 PROBLEM: Retry on success due to bad exception handling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        attempt_count = [0]

        @app.task(bind=True, max_retries=3, autoretry_for=(Exception,))
        def bad_retry_task(self, order_id):
            """Task that retries on ANY exception, even transient ones."""
            attempt_count[0] += 1
            order = Order.objects.get(pk=order_id)
            self.stdout.write(f'  Attempt {attempt_count[0]}: Processing order')

            if attempt_count[0] == 1:
                self.stdout.write('    -> First try: raises generic Exception')
                raise Exception('Transient error')

            # Second attempt succeeds
            self.stdout.write(f'    -> Success!')
            return 'done'

        order = Order.objects.create(
            order_number='Q41-ORDER',
            customer_email='q41@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask with autoretry_for=(Exception,):')
        try:
            bad_retry_task(order.pk)
        except Exception as e:
            self.stdout.write(f'  Exception: {e}')

        self.stdout.write(self.style.WARNING(
            f'\nPROBLEM: Task retried {attempt_count[0]} times:\n'
            '  - Attempt 1: raised Exception -> auto-retried\n'
            '  - Attempt 2: succeeded, but still marked for retry\n'
            '  - Duplicate work and late success'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Duplicate operations on success')
        self.stdout.write('  - Queue backlog from unnecessary retries')
        self.stdout.write('  - Delayed responses')
