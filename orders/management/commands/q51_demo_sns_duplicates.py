from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q51 PROBLEM: SNS/SQS delivers messages at-least-once. Without idempotency
    checks, your consumer processes the same message multiple times, causing
    duplicate charges, duplicate emails, or corrupted data.
    """
    help = 'Q51 Problem: Duplicate SNS/SQS messages processed multiple times'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q51 PROBLEM: No idempotency - duplicates processed')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q51-ORDER',
            customer_email='q51@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        def charge_card_no_idempotency(message_body):
            """Processes payment without checking for duplicates."""
            order_id = message_body['order_id']
            amount = message_body['amount']
            self.stdout.write(self.style.ERROR(
                f'  Charging ${amount} for order {order_id}'
            ))
            return f'charged_{amount}'

        # Simulate SNS delivering same message twice (common in prod)
        message = {'order_id': order.pk, 'amount': '100.00', 'message_id': 'msg-abc-123'}

        self.stdout.write('SNS delivers message (first delivery):')
        charge_card_no_idempotency(message)

        self.stdout.write('\nSNS re-delivers same message (network issue):')
        charge_card_no_idempotency(message)

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Customer charged twice!\n'
            '  - SNS at-least-once delivery is expected behaviour\n'
            '  - Without idempotency check, duplicates cause real harm\n'
            '  - No way to detect the second message is a duplicate'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SNS/SQS guarantees at-least-once, NOT exactly-once')
        self.stdout.write('  - Always assume messages will be delivered multiple times')
        self.stdout.write('  - Every consumer must have idempotency protection')
