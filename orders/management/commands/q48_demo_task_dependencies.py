from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q48 PROBLEM: Task dependencies (group, chain, chord) not tracked in DB.
    If parent task fails, child tasks (subtasks) are orphaned and continue
    executing. No visibility into task hierarchy.
    """
    help = 'Q48 Problem: Untracked task dependencies'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q48 PROBLEM: Orphaned subtasks')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def validate_order(order_id):
            return 'valid'

        @app.task
        def process_payment(order_id, validation_result):
            return 'charged'

        @app.task
        def send_confirmation(order_id, payment_result):
            return 'sent'

        order = Order.objects.create(
            order_number='Q48-ORDER',
            customer_email='q48@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Chain of tasks:')
        self.stdout.write('  1. validate_order(order_id)')
        self.stdout.write('  2. process_payment(order_id, validation_result)')
        self.stdout.write('  3. send_confirmation(order_id, payment_result)')
        self.stdout.write('')
        self.stdout.write('Scenario: validate_order fails')
        self.stdout.write('  - process_payment still enqueued')
        self.stdout.write('  - send_confirmation still enqueued')
        self.stdout.write('  - User charged with invalid order!')
        self.stdout.write('  - Email sent for order that failed')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No parent-child tracking\n'
            '  - Orphaned subtasks execute anyway\n'
            '  - Can result in partial failures\n'
            '  - Data inconsistency'
        ))
