from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
from datetime import datetime
import json


class Command(BaseCommand):
    """
    Q39 PROBLEM: Celery's default JSON serialization cannot handle Decimal,
    datetime, or custom types. Attempting to pass these to tasks causes
    TypeError or data corruption. This is a silent failure mode that's
    hard to debug.
    """
    help = 'Q39 Problem: JSON serialization fails for non-standard types'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q39 PROBLEM: JSON serialization incompatibility')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        tax = Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def process_with_decimal(amount):
            """Task expecting Decimal parameter."""
            self.stdout.write(f'  Amount (type {type(amount).__name__}): {amount}')
            return float(amount)

        order = Order.objects.create(
            order_number='Q39-ORDER',
            customer_email='q39@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTrying to pass Decimal to task:')
        try:
            self.stdout.write(f'  Passing amount={order.amount} (Decimal type)')
            json.dumps({'amount': order.amount})
        except TypeError as e:
            self.stdout.write(self.style.ERROR(
                f'  TypeError: Object of type Decimal is not JSON serializable'
            ))

        self.stdout.write('\nSimilarly, datetime fails:')
        try:
            json.dumps({'created': datetime.now()})
        except TypeError:
            self.stdout.write(self.style.ERROR(
                '  TypeError: Object of type datetime is not JSON serializable'
            ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Task serialization fails:\n'
            '  - Decimal type not JSON serializable\n'
            '  - datetime objects can\'t be passed directly\n'
            '  - Custom types silently drop or corrupt\n'
            '  - Task never reaches worker'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Data loss (values silently become strings or null)')
        self.stdout.write('  - Hard to debug (failure is in serialization layer)')
        self.stdout.write('  - May work in development (direct call) but fail in production')
