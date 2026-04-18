from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q26 SOLUTION: Use an idempotency key (stored in DB) to detect and skip
    duplicate executions. The task checks if it has already run for this
    idempotency key before performing the side effect.
    """
    help = 'Q26 Solution: Idempotency key prevents duplicate operations'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q26 SOLUTION: Idempotency key pattern')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Track executed tasks (in production: use a DB table)
        executed_tasks = {}

        @app.task
        def idempotent_charge(order_id, idempotency_key):
            """
            Idempotent task: checks if already processed before charging.
            Subsequent retries see the key and skip the charge.
            """
            if idempotency_key in executed_tasks:
                self.stdout.write(
                    f'  [Task] Idempotency key {idempotency_key} already seen. Skipping charge.'
                )
                return {'charged': 0.0, 'duplicate': True}

            order = Order.objects.get(pk=order_id)
            charge_amount = order.amount
            executed_tasks[idempotency_key] = True
            self.stdout.write(f'  [Task] First run: charged ${charge_amount}')
            return {'charged': float(charge_amount), 'duplicate': False}

        order = Order.objects.create(
            order_number='Q26-SOL-ORDER',
            customer_email='q26sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk} for $100.00')

        idempotency_key = f'charge-{order.pk}-uuid-12345'
        self.stdout.write(f'\nUsing idempotency key: {idempotency_key}')

        self.stdout.write('Execution 1 (original):')
        idempotent_charge(order.pk, idempotency_key)

        self.stdout.write('\nWorker crashed. Broker requeued task.')
        self.stdout.write('Execution 2 (retry):')
        idempotent_charge(order.pk, idempotency_key)

        self.stdout.write(self.style.SUCCESS(
            '\nCustomer charged only ONCE ($100), despite duplicate execution!'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Every Celery task must be idempotent')
        self.stdout.write('  - Use a unique idempotency key (UUID, fingerprint)')
        self.stdout.write('  - Store processed keys in DB or cache')
        self.stdout.write('  - Return same result on duplicate runs')
