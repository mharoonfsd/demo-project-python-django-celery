from decimal import Decimal
import time
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q52 PROBLEM: SQS visibility timeout is the time a message is hidden from
    other consumers while being processed. If your task takes longer than the
    timeout, SQS makes the message visible again — another worker picks it up,
    causing duplicate processing.
    """
    help = 'Q52 Problem: Visibility timeout too short causes redelivery'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q52 PROBLEM: Visibility timeout too short')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q52-ORDER',
            customer_email='q52@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        VISIBILITY_TIMEOUT = 3   # seconds (normally 30s default)
        TASK_DURATION = 5        # seconds (longer than timeout!)

        self.stdout.write(f'SQS Queue config:')
        self.stdout.write(f'  VisibilityTimeout = {VISIBILITY_TIMEOUT}s')
        self.stdout.write(f'  Task processing time = {TASK_DURATION}s')
        self.stdout.write('')

        self.stdout.write('Worker-A receives message at t=0...')
        self.stdout.write(f'  Message hidden for {VISIBILITY_TIMEOUT}s')

        self.stdout.write(f'\n[t={VISIBILITY_TIMEOUT}s] Visibility timeout expires!')
        self.stdout.write(self.style.WARNING(
            '  Message becomes visible again in SQS'
        ))
        self.stdout.write('Worker-B picks up same message...')
        self.stdout.write(self.style.ERROR(
            '  DUPLICATE PROCESSING: Both Worker-A and Worker-B are now\n'
            '  processing the same message concurrently!'
        ))
        self.stdout.write(f'\n[t={TASK_DURATION}s] Worker-A finishes (too late)')
        self.stdout.write('  Worker-A deletes message - but Worker-B already processed it')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Duplicate processing due to short timeout\n'
            '  - Customer charged twice\n'
            '  - Email sent twice\n'
            '  - Data corrupted'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Default SQS VisibilityTimeout = 30s')
        self.stdout.write('  - Must be > max task processing time')
        self.stdout.write('  - Set to 6x your average processing time')
        self.stdout.write('  - Extend timeout during processing with ChangeMessageVisibility')
