from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q49 PROBLEM: Without rate limiting, a single spike in traffic can
    overwhelm workers and queue, causing timeouts and customer impact.
    Tasks pile up faster than workers can process them.
    """
    help = 'Q49 Problem: No rate limiting on tasks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q49 PROBLEM: No rate limiting')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def send_email(order_id):
            """Task with no rate limit."""
            return 'sent'

        order = Order.objects.create(
            order_number='Q49-ORDER',
            customer_email='q49@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Scenario: Flash sale marketing campaign')
        self.stdout.write('  Normal traffic: 100 orders/min')
        self.stdout.write('  Marketing sends email: 10,000 orders/hour')
        self.stdout.write('  Each order triggers send_email task')
        self.stdout.write('')
        self.stdout.write('Result without rate limiting:')
        self.stdout.write('  - Queue swells to 10,000+ tasks')
        self.stdout.write('  - Workers backlogged for hours')
        self.stdout.write('  - Other urgent tasks delayed')
        self.stdout.write('  - Email quota exhausted')
        self.stdout.write('  - API throttling errors')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Uncontrolled queue growth\n'
            '  - Queue depth explodes\n'
            '  - Service degradation\n'
            '  - Rate limits exceeded'
        ))
