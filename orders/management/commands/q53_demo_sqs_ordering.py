from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q53 PROBLEM: SQS standard queues do NOT guarantee ordering. Messages sent
    in order A -> B -> C may arrive as C -> A -> B. Systems that assume order
    (e.g., state machines, event sourcing) will break silently.
    """
    help = 'Q53 Problem: SQS standard queue - no ordering guarantee'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q53 PROBLEM: SQS standard queue - unordered delivery')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q53-ORDER',
            customer_email='q53@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate out-of-order delivery from SQS standard queue
        sent_events = [
            {'seq': 1, 'event': 'order_created', 'order_id': order.pk},
            {'seq': 2, 'event': 'payment_captured', 'order_id': order.pk},
            {'seq': 3, 'event': 'order_shipped', 'order_id': order.pk},
        ]

        # SQS standard queue may deliver in any order
        received_events = [
            {'seq': 3, 'event': 'order_shipped', 'order_id': order.pk},
            {'seq': 1, 'event': 'order_created', 'order_id': order.pk},
            {'seq': 2, 'event': 'payment_captured', 'order_id': order.pk},
        ]

        self.stdout.write('Events sent (in order):')
        for e in sent_events:
            self.stdout.write(f'  seq={e["seq"]} {e["event"]}')

        self.stdout.write('\nEvents received from SQS (out of order!):')
        order_state = 'none'
        for e in received_events:
            self.stdout.write(f'  seq={e["seq"]} {e["event"]}')
            if e['event'] == 'order_shipped' and order_state == 'none':
                self.stdout.write(self.style.ERROR(
                    '    ERROR: Cannot ship order that was never created!'
                ))
                order_state = 'invalid'

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Out-of-order events cause state machine corruption\n'
            '  - Shipped before payment captured\n'
            '  - Created after shipped\n'
            '  - Impossible to reconstruct correct state'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SQS standard: at-least-once, best-effort ordering')
        self.stdout.write('  - SQS FIFO: exactly-once, strict ordering (slower)')
        self.stdout.write('  - Include sequence numbers or timestamps in messages')
        self.stdout.write('  - Design consumers to handle out-of-order messages')
