from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q56 SOLUTION: Use MaxNumberOfMessages=10 in ReceiveMessage and
    DeleteMessageBatch for batch deletes. Reduces API calls by 10x.
    """
    help = 'Q56 Solution: Batch SQS message processing'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q56 SOLUTION: Batch SQS receive and delete')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q56-SOL-{i:03}',
                customer_email=f'q56sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        total_messages = 10
        batch_size = 10

        # Batch receive
        api_calls_receive = (total_messages + batch_size - 1) // batch_size
        # Batch delete
        api_calls_delete = (total_messages + batch_size - 1) // batch_size

        self.stdout.write('Processing 10 messages IN BATCHES of 10:')
        self.stdout.write(f'  Messages processed: {total_messages}')
        self.stdout.write(f'  ReceiveMessage API calls: {api_calls_receive}')
        self.stdout.write(f'  DeleteMessageBatch API calls: {api_calls_delete}')
        total_cost_calls = api_calls_receive + api_calls_delete
        self.stdout.write(self.style.SUCCESS(
            f'  Total API calls: {total_cost_calls} (vs 20 without batching)'
        ))

        sqs_price_per_million = 0.40
        monthly_messages = 1_000_000
        monthly_api_calls_good = (monthly_messages // batch_size) * 2
        monthly_cost_good = (monthly_api_calls_good / 1_000_000) * sqs_price_per_million

        self.stdout.write(f'\nAt 1M messages/month:')
        self.stdout.write(f'  API calls (with batch): {monthly_api_calls_good:,}')
        self.stdout.write(self.style.SUCCESS(
            f'  Monthly SQS cost: ${monthly_cost_good:.2f} (vs $0.80 without batch)'
        ))

        self.stdout.write('\nCode example (boto3):')
        self.stdout.write('  # Batch receive')
        self.stdout.write('  response = sqs.receive_message(')
        self.stdout.write('      QueueUrl=queue_url,')
        self.stdout.write('      MaxNumberOfMessages=10,     # <-- key change')
        self.stdout.write('      WaitTimeSeconds=20,          # long polling')
        self.stdout.write('  )')
        self.stdout.write('  messages = response.get("Messages", [])')
        self.stdout.write('')
        self.stdout.write('  # Process all messages')
        self.stdout.write('  for message in messages:')
        self.stdout.write('      process(message)')
        self.stdout.write('')
        self.stdout.write('  # Batch delete')
        self.stdout.write('  entries = [{"Id": str(i), "ReceiptHandle": m["ReceiptHandle"]}')
        self.stdout.write('             for i, m in enumerate(messages)]')
        self.stdout.write('  sqs.delete_message_batch(QueueUrl=queue_url, Entries=entries)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use MaxNumberOfMessages=10 in ReceiveMessage')
        self.stdout.write('  - Use DeleteMessageBatch for bulk deletes')
        self.stdout.write('  - Combine with long polling (WaitTimeSeconds=20)')
        self.stdout.write('  - 10x reduction in API calls = 10x cost reduction')
