from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q51 SOLUTION: Track processed message IDs in DB. Before processing,
    check if message_id already exists. Use DB unique constraint to prevent
    race conditions between workers.
    """
    help = 'Q51 Solution: Idempotency keys prevent duplicate processing'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q51 SOLUTION: Idempotency key prevents duplicates')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q51-SOL-ORDER',
            customer_email='q51sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate processed message ID store (in production: Redis SET or DB table)
        processed_ids = set()

        def charge_card_idempotent(message_body):
            """Processes payment with idempotency check."""
            message_id = message_body['message_id']
            order_id = message_body['order_id']
            amount = message_body['amount']

            if message_id in processed_ids:
                self.stdout.write(self.style.WARNING(
                    f'  Skipping duplicate message_id={message_id}'
                ))
                return 'skipped_duplicate'

            # Mark as processed BEFORE doing work (prevents race)
            processed_ids.add(message_id)
            self.stdout.write(self.style.SUCCESS(
                f'  Charging ${amount} for order {order_id} [msg={message_id}]'
            ))
            return f'charged_{amount}'

        message = {'order_id': order.pk, 'amount': '100.00', 'message_id': 'msg-abc-123'}

        self.stdout.write('First delivery:')
        result1 = charge_card_idempotent(message)
        self.stdout.write(f'  Result: {result1}')

        self.stdout.write('\nDuplicate delivery:')
        result2 = charge_card_idempotent(message)
        self.stdout.write(f'  Result: {result2}')

        self.stdout.write(self.style.SUCCESS(
            '\nSUCCESS: Customer charged exactly once!'
        ))

        self.stdout.write('\nProduction implementation:')
        self.stdout.write('  Option 1: Redis SET with TTL')
        self.stdout.write('    redis.set(f"processed:{msg_id}", 1, ex=86400)')
        self.stdout.write('  Option 2: DB table with unique constraint')
        self.stdout.write('    ProcessedMessage(message_id=msg_id).save()')
        self.stdout.write('  Option 3: Conditional DB update')
        self.stdout.write('    Order.objects.filter(id=id, processed=False).update(processed=True)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Store message_id in Redis/DB before processing')
        self.stdout.write('  - Check idempotency key BEFORE doing work')
        self.stdout.write('  - Use DB unique constraint as final safety net')
        self.stdout.write('  - Set TTL on idempotency keys (24h typical)')
