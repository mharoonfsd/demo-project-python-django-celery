from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q57 PROBLEM: Short polling returns immediately even if the queue is empty.
    It wastes API calls and creates unnecessary load. In production with SQS,
    short polling costs 10x more and causes tight CPU-spinning loops.
    """
    help = 'Q57 Problem: Short polling SQS - empty responses, wasted API calls'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q57 PROBLEM: SQS short polling (empty responses)')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        self.stdout.write('Simulating 10 seconds of short polling:')
        self.stdout.write('  (WaitTimeSeconds=0, default, short polling)')
        self.stdout.write('')

        api_calls = 0
        empty_responses = 0
        messages_received = 0

        # Simulate: queue has messages only at t=5 and t=9
        messages_at_seconds = {5: 3, 9: 2}

        for t in range(10):
            api_calls += 1
            msgs = messages_at_seconds.get(t, 0)
            if msgs > 0:
                messages_received += msgs
                self.stdout.write(f'  t={t}s: ReceiveMessage -> {msgs} messages')
            else:
                empty_responses += 1
                self.stdout.write(f'  t={t}s: ReceiveMessage -> EMPTY (wasted call)')

        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Total API calls: {api_calls}')
        self.stdout.write(f'  Empty responses: {empty_responses}')
        self.stdout.write(f'  Messages received: {messages_received}')
        waste_pct = (empty_responses / api_calls) * 100
        self.stdout.write(self.style.ERROR(
            f'  Wasted API calls: {waste_pct:.0f}%'
        ))

        cost_per_million = 0.40
        monthly_api_calls = api_calls * 6 * 60 * 24 * 30  # scale to 1 month
        monthly_cost = (monthly_api_calls / 1_000_000) * cost_per_million
        self.stdout.write(self.style.ERROR(
            f'  Estimated monthly cost: ${monthly_cost:.2f}'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - WaitTimeSeconds=0 (default) = short polling')
        self.stdout.write('  - Short polling only checks a subset of SQS servers')
        self.stdout.write('  - Causes empty responses even when messages exist')
        self.stdout.write('  - Use WaitTimeSeconds=20 (long polling) in production')
