from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q56 PROBLEM: Processing messages one at a time from SQS is extremely
    slow and wastes API calls. Each ReceiveMessage call fetches 1 message
    but could fetch up to 10. Deleting one at a time is even worse.
    """
    help = 'Q56 Problem: SQS single-message polling - slow and expensive'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q56 PROBLEM: SQS single-message processing (no batching)')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q56-ORD-{i:03}',
                customer_email=f'q56user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        total_messages = 10
        api_calls_receive = 0
        api_calls_delete = 0
        processed = 0

        self.stdout.write('Processing 10 messages ONE AT A TIME (no batch):')
        for i in range(total_messages):
            api_calls_receive += 1  # one API call per message
            processed += 1
            api_calls_delete += 1   # one delete API call per message

        self.stdout.write(f'  Messages processed: {processed}')
        self.stdout.write(f'  ReceiveMessage API calls: {api_calls_receive}')
        self.stdout.write(f'  DeleteMessage API calls: {api_calls_delete}')
        total_cost_calls = api_calls_receive + api_calls_delete
        self.stdout.write(self.style.ERROR(
            f'  Total API calls: {total_cost_calls}'
        ))

        sqs_price_per_million = 0.40  # USD
        monthly_messages = 1_000_000
        monthly_api_calls_bad = monthly_messages * 2  # receive + delete
        monthly_cost_bad = (monthly_api_calls_bad / 1_000_000) * sqs_price_per_million

        self.stdout.write(f'\nAt 1M messages/month:')
        self.stdout.write(f'  API calls (no batch): {monthly_api_calls_bad:,}')
        self.stdout.write(self.style.ERROR(
            f'  Monthly SQS cost: ${monthly_cost_bad:.2f}'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SQS allows up to 10 messages per ReceiveMessage call')
        self.stdout.write('  - DeleteMessageBatch handles up to 10 deletes per call')
        self.stdout.write('  - Single-message mode = 10x more API calls')
        self.stdout.write('  - Use MaxNumberOfMessages=10 in ReceiveMessage')
