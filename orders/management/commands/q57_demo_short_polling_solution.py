from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q57 SOLUTION: Use WaitTimeSeconds=20 (long polling). SQS waits up to 20s
    for messages to arrive before returning empty. Reduces API calls by 90%.
    """
    help = 'Q57 Solution: SQS long polling with WaitTimeSeconds=20'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q57 SOLUTION: SQS long polling (WaitTimeSeconds=20)')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        self.stdout.write('Simulating 10 seconds of long polling:')
        self.stdout.write('  (WaitTimeSeconds=20, blocks up to 20s per call)')
        self.stdout.write('')

        # With long polling: SQS blocks until messages arrive or 20s passes
        # Effectively, one API call per message batch
        messages_at_seconds = {5: 3, 9: 2}

        api_calls = 0
        messages_received = 0
        t = 0
        while t < 10:
            api_calls += 1
            # Find next message time or advance 20s
            next_msg_time = min((s for s in messages_at_seconds if s >= t), default=None)
            if next_msg_time is not None and next_msg_time < t + 20:
                wait_time = next_msg_time - t
                msgs = messages_at_seconds[next_msg_time]
                messages_received += msgs
                self.stdout.write(self.style.SUCCESS(
                    f'  Long poll: blocked {wait_time}s -> {msgs} messages received'
                ))
                t = next_msg_time + 1
            else:
                self.stdout.write(f'  Long poll: blocked 20s -> EMPTY')
                t += 20

        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Total API calls: {api_calls}')
        self.stdout.write(f'  Messages received: {messages_received}')
        self.stdout.write(self.style.SUCCESS(
            f'  Zero wasted empty responses!'
        ))

        short_poll_calls = 10
        long_poll_calls = api_calls
        saving_pct = (1 - long_poll_calls / short_poll_calls) * 100
        self.stdout.write(self.style.SUCCESS(
            f'  API call reduction: {saving_pct:.0f}% vs short polling'
        ))

        self.stdout.write('\nCode example:')
        self.stdout.write('  response = sqs.receive_message(')
        self.stdout.write('      QueueUrl=queue_url,')
        self.stdout.write('      MaxNumberOfMessages=10,')
        self.stdout.write('      WaitTimeSeconds=20,  # <-- long polling')
        self.stdout.write('  )')

        self.stdout.write('\nQueue-level long polling (applies to all consumers):')
        self.stdout.write('  sqs.set_queue_attributes(')
        self.stdout.write('      QueueUrl=queue_url,')
        self.stdout.write('      Attributes={"ReceiveMessageWaitTimeSeconds": "20"}')
        self.stdout.write('  )')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use WaitTimeSeconds=20 (max) in production')
        self.stdout.write('  - Or set ReceiveMessageWaitTimeSeconds on the queue itself')
        self.stdout.write('  - Long polling checks all SQS servers (fewer false empties)')
        self.stdout.write('  - Combine with MaxNumberOfMessages=10 for max efficiency')
