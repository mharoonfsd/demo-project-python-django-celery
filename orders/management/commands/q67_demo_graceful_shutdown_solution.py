from decimal import Decimal
import threading
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q67 SOLUTION: Handle SIGTERM to stop accepting new messages and drain
    in-flight messages before exiting. ECS gives stopTimeout (default 30s)
    before SIGKILL — use it to finish current work.
    """
    help = 'Q67 Solution: Graceful shutdown drains in-flight messages'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q67 SOLUTION: Graceful shutdown on SIGTERM')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q67-SOL-{i:03}',
                customer_email=f'q67sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        shutdown_flag = threading.Event()
        deleted = []
        returned_to_queue = []

        def graceful_consumer():
            """Consumer that handles SIGTERM gracefully."""
            batch = [
                {'id': 'msg-1', 'order_id': 1},
                {'id': 'msg-2', 'order_id': 2},
                {'id': 'msg-3', 'order_id': 3},
            ]

            for i, msg in enumerate(batch):
                if shutdown_flag.is_set():
                    self.stdout.write(self.style.WARNING(
                        f'  Shutdown signalled - returning {msg["id"]} to queue'
                    ))
                    returned_to_queue.append(msg['id'])
                    # change_message_visibility(receipt_handle, 0) makes it visible immediately
                    continue

                self.stdout.write(f'  Processing {msg["id"]}...')

                if i == 1:
                    # Simulate SIGTERM arrives while processing msg-2
                    shutdown_flag.set()
                    self.stdout.write(self.style.WARNING(
                        '  [SIGTERM received] Finishing current message, then draining...'
                    ))

                # Complete current message (already in progress)
                deleted.append(msg['id'])
                self.stdout.write(self.style.SUCCESS(f'  {msg["id"]} completed and deleted'))

        graceful_consumer()

        self.stdout.write(f'\nCompleted and deleted: {deleted}')
        self.stdout.write(f'Returned to queue (will be picked up by another worker): {returned_to_queue}')
        self.stdout.write(self.style.SUCCESS(
            '\nResult: Clean handoff - no data loss, no duplicates'
        ))

        self.stdout.write('\nPython SIGTERM handler implementation:')
        self.stdout.write('  import signal')
        self.stdout.write('  shutdown = threading.Event()')
        self.stdout.write('  signal.signal(signal.SIGTERM, lambda s, f: shutdown.set())')
        self.stdout.write('')
        self.stdout.write('  while not shutdown.is_set():')
        self.stdout.write('      messages = sqs.receive_message(...)')
        self.stdout.write('      for msg in messages:')
        self.stdout.write('          if shutdown.is_set(): return_to_queue(msg); continue')
        self.stdout.write('          process(msg)')
        self.stdout.write('          delete_message(msg)')

        self.stdout.write('\nECS task definition setting:')
        self.stdout.write('  stopTimeout: 60  # seconds (default 30)')
        self.stdout.write('  Give enough time to drain in-flight messages')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Handle SIGTERM: set shutdown flag, stop accepting new work')
        self.stdout.write('  - Finish current in-flight messages before exiting')
        self.stdout.write('  - Return unstarted messages to queue immediately')
        self.stdout.write('  - Set ECS stopTimeout > your max message processing time')
