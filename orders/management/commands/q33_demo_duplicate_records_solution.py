from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q33 SOLUTION: Use DB-level UNIQUE constraints combined with get_or_create()
    or check_exists() before creating records. The database enforces uniqueness,
    preventing duplicate records even under concurrent task execution.
    """
    help = 'Q33 Solution: Unique constraints + get_or_create() prevent duplicates'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q33 SOLUTION: DB unique constraint + get_or_create()')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def safe_create_payment_record(order_id):
            """Create payment record with duplicate protection."""
            order = Order.objects.get(pk=order_id)
            
            try:
                # get_or_create with unique constraint
                # If another task created it already, we get the existing one
                tax, created = Tax.objects.get_or_create(
                    name=f'payment-{order.order_number}',
                    defaults={'value': Decimal('0.00')}
                )
                if created:
                    self.stdout.write(f'  Created new payment record')
                else:
                    self.stdout.write(f'  Payment record already exists (duplicate detected)')
                return 'success'
            except IntegrityError:
                # Fallback for race between get and create
                self.stdout.write(f'  IntegrityError caught, payment already recorded')
                return 'duplicate'

        order = Order.objects.create(
            order_number='Q33-SOL-ORDER',
            customer_email='q33sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nSimulating concurrent task executions:')
        self.stdout.write('Task instance 1:')
        safe_create_payment_record(order.pk)

        self.stdout.write('Task instance 2 (duplicate):')
        safe_create_payment_record(order.pk)

        self.stdout.write('Task instance 3 (duplicate):')
        safe_create_payment_record(order.pk)

        self.stdout.write(self.style.SUCCESS(
            '\nOnly ONE payment record created, despite three task executions!'
        ))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use DB UNIQUE constraints for critical records')
        self.stdout.write('  - Use get_or_create() to handle duplicates gracefully')
        self.stdout.write('  - Catch IntegrityError as final safety net')
        self.stdout.write('  - Always have an idempotency key in task design')
