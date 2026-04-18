from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q62 SOLUTION: Use idempotency key stored in DB before processing.
    Even if consumer crashes and message is redelivered, the second
    attempt detects the key and skips reprocessing.
    """
    help = 'Q62 Solution: Idempotent consumer survives crash + redelivery'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q62 SOLUTION: Idempotent consumer handles crash + redelivery')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q62-SOL-ORDER',
            customer_email='q62sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        processed_keys = set()  # simulates Redis/DB idempotency store
        charged_log = []

        def process_idempotent(message, attempt, simulate_crash=False):
            msg_id = message['message_id']
            order_id = message['order_id']

            self.stdout.write(f'\nAttempt {attempt}: received message {msg_id}')

            # Check idempotency before ANY work
            if msg_id in processed_keys:
                self.stdout.write(self.style.WARNING(
                    f'  Duplicate detected (msg_id={msg_id}) - skipping'
                ))
                return 'skipped'

            # Perform work
            charged_log.append(order_id)
            self.stdout.write(f'  Charging order {order_id}...')
            self.stdout.write(self.style.SUCCESS('  Payment captured!'))

            if simulate_crash:
                # Mark idempotency key BEFORE crash-prone operations complete
                # Actually in real code, use DB transaction to mark + work atomically
                processed_keys.add(msg_id)
                raise RuntimeError('Container restarted (but key was saved!)')

            processed_keys.add(msg_id)
            self.stdout.write('  Message deleted from SQS')
            return 'processed'

        message = {'order_id': order.pk, 'message_id': 'msg-xyz-safe'}

        try:
            process_idempotent(message, 1, simulate_crash=True)
        except RuntimeError as e:
            self.stdout.write(self.style.WARNING(f'  Crashed: {e}'))
            self.stdout.write('  SQS redelivers message...')

        process_idempotent(message, 2, simulate_crash=False)

        self.stdout.write(self.style.SUCCESS(
            f'\nSUCCESS: Payment charged exactly once!'
        ))
        self.stdout.write(f'  Charge log: {charged_log}')

        self.stdout.write('\nBest practice - atomic idempotency with DB transaction:')
        self.stdout.write('  with transaction.atomic():')
        self.stdout.write('      # This fails if already processed (unique constraint)')
        self.stdout.write('      ProcessedMessage.objects.create(message_id=msg_id)')
        self.stdout.write('      # Now safe to do work')
        self.stdout.write('      charge_card(order_id)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Store idempotency key BEFORE or ATOMICALLY WITH work')
        self.stdout.write('  - Use DB unique constraint as crash-safe idempotency lock')
        self.stdout.write('  - Redis SET NX with TTL works for high-throughput cases')
        self.stdout.write('  - Test crash scenarios explicitly in your CI pipeline')
