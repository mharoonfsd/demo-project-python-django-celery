from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import models
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q26 PROBLEM: Celery uses at-least-once delivery semantics. If a worker
    crashes after processing a task but before acknowledging it, the broker
    re-queues the task. Without an idempotency key, the task runs again,
    causing duplicate operations (double charges, duplicate emails, etc.).
    """
    help = 'Q26 Problem: At-least-once delivery causes duplicate task execution'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q26 PROBLEM: At-least-once delivery, duplicates without idempotency')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Define a non-idempotent task
        @app.task
        def non_idempotent_charge(order_id):
            """Each call charges the customer. Running twice = double charge!"""
            order = Order.objects.get(pk=order_id)
            charge_amount = order.amount
            # Simulate: charging customer's payment method
            self.stdout.write(f'  [Task] Charged ${charge_amount} from customer')
            return {'charged': float(charge_amount)}

        order = Order.objects.create(
            order_number='Q26-ORDER',
            customer_email='q26@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk} for $100.00')

        self.stdout.write('\nSimulating task execution (at-least-once semantics):')
        self.stdout.write('Execution 1 (original attempt):')
        non_idempotent_charge(order.pk)

        self.stdout.write('\nWorker crashed before ACK. Broker requeued task.')
        self.stdout.write('Execution 2 (retry after crash):')
        non_idempotent_charge(order.pk)

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Customer charged TWICE ($200 total) for a single order!'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Customer charged multiple times for one purchase')
        self.stdout.write('  - Duplicate emails sent')
        self.stdout.write('  - Inventory decremented multiple times')
        self.stdout.write('  - Hard to detect and refund')
