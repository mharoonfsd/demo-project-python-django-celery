from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q61 PROBLEM: A poison message causes the consumer to crash on every
    attempt. Without handling it specially, the message loops endlessly
    between the queue and the consumer, blocking all other messages.
    """
    help = 'Q61 Problem: Poison message causes infinite retry loop'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q61 PROBLEM: Poison message - infinite retry loop')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q61-ORDER',
            customer_email='q61@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        messages = [
            {'id': 'msg-1', 'order_id': 1, 'receive_count': 1},
            {'id': 'msg-poison', 'order_id': None, 'malformed': True, 'receive_count': 15},
            {'id': 'msg-3', 'order_id': 3, 'receive_count': 1},
        ]

        def process_without_poison_handling(msg):
            """Consumer has no poison message detection."""
            if msg.get('malformed'):
                raise ValueError(f'Cannot process malformed message {msg["id"]}')
            return f'processed order {msg["order_id"]}'

        self.stdout.write('Consumer processing queue (no poison message handling):')
        for msg in messages:
            try:
                result = process_without_poison_handling(msg)
                self.stdout.write(self.style.SUCCESS(f'  {msg["id"]}: {result}'))
            except ValueError as e:
                self.stdout.write(self.style.ERROR(
                    f'  {msg["id"]}: FAILED - {e}'
                ))
                self.stdout.write(self.style.ERROR(
                    f'    receive_count={msg["receive_count"]} - message will retry forever!'
                ))
                self.stdout.write(self.style.WARNING(
                    f'    msg-3 is BLOCKED behind the poison message'
                ))
                break  # Simulate message going back to queue blocking others

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Poison message blocks queue processing\n'
            '  - msg-poison has been received 15 times and still fails\n'
            '  - msg-3 never gets processed (FIFO blockage)\n'
            '  - Worker keeps crashing and restarting\n'
            '  - No alerting, no visibility into root cause'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Malformed messages will ALWAYS fail - retry is futile')
        self.stdout.write('  - Must detect and route poison messages to DLQ')
        self.stdout.write('  - Check receive_count before processing')
        self.stdout.write('  - Alert immediately when DLQ receives messages')
