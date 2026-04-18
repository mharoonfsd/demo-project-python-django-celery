from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q33 PROBLEM: Duplicate task executions within a distributed system can
    cause data anomalies. Without a unique constraint or idempotency check,
    multiple workers can all execute the same task with different outcomes.
    """
    help = 'Q33 Problem: Duplicate task execution without unique constraint'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q33 PROBLEM: Duplicate task execution anomalies')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def unprotected_create_payment_record(order_id):
            """Create payment record without duplicate protection."""
            order = Order.objects.get(pk=order_id)
            # BUG: No check for existing record
            # Multiple concurrent tasks all create records
            payment_count = Order.objects.filter(order_number=order.order_number).count()
            self.stdout.write(f'  Created payment record #{payment_count}')
            return payment_count

        order = Order.objects.create(
            order_number='Q33-ORDER',
            customer_email='q33@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nSimulating concurrent task executions:')
        self.stdout.write('Task instance 1:')
        unprotected_create_payment_record(order.pk)

        self.stdout.write('Task instance 2 (duplicate):')
        unprotected_create_payment_record(order.pk)

        self.stdout.write('Task instance 3 (duplicate):')
        unprotected_create_payment_record(order.pk)

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Multiple payment records created for single order!\n'
            '  - Record 1: created by task instance 1\n'
            '  - Record 2: created by task instance 2 (duplicate)\n'
            '  - Record 3: created by task instance 3 (duplicate)\n'
            'This is a data integrity error.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Payment records duplicated in accounting system')
        self.stdout.write('  - Invoices generated multiple times')
        self.stdout.write('  - Difficult to detect and reconcile')
