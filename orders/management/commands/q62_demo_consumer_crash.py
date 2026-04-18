from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q62 PROBLEM: Consumer crashes mid-processing without deleting the message.
    The message becomes visible again after the visibility timeout and is
    reprocessed. Without idempotency, this causes double processing.
    """
    help = 'Q62 Problem: Consumer crash mid-processing causes redelivery'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q62 PROBLEM: Consumer crash - message redelivered')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q62-ORDER',
            customer_email='q62@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        charged_log = []

        def charge_and_crash(order_id):
            """Charges card then crashes before deleting the SQS message."""
            charged_log.append(order_id)
            self.stdout.write(f'  Charging order {order_id}...')
            self.stdout.write(self.style.SUCCESS(f'  Payment captured!'))
            # Simulate crash before message deletion
            raise RuntimeError('OOM: Container killed before delete_message()')

        def consumer_without_idempotency(message, attempt):
            self.stdout.write(f'\nAttempt {attempt}: received message for order {message["order_id"]}')
            try:
                charge_and_crash(message['order_id'])
                # delete_message() never reached
            except RuntimeError as e:
                self.stdout.write(self.style.ERROR(f'  Consumer crashed: {e}'))
                self.stdout.write('  Message becomes visible again in SQS after timeout...')

        message = {'order_id': order.pk, 'message_id': 'msg-xyz'}

        consumer_without_idempotency(message, 1)
        consumer_without_idempotency(message, 2)  # redelivery after crash

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Payment charged {len(charged_log)} times!'
        ))
        self.stdout.write(f'  Charge log: {charged_log}')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Crashes before delete_message = guaranteed redelivery')
        self.stdout.write('  - All SQS consumers must be idempotent (see Q51)')
        self.stdout.write('  - Use DB transaction + idempotency key before charging')
        self.stdout.write('  - Design for "at-least-once" - it WILL happen in production')
