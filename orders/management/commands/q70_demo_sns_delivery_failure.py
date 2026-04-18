from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q70 PROBLEM: SNS topic has too many subscriptions but no subscriber
    health tracking. Failed deliveries silently disappear. No dead-letter
    topic configured on SNS. No visibility into delivery failures.
    """
    help = 'Q70 Problem: SNS delivery failures with no dead-letter topic'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q70 PROBLEM: SNS delivery failures - no dead-letter topic')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q70-ORDER',
            customer_email='q70@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate SNS publishing to multiple subscribers
        subscriptions = [
            {'name': 'email-service-sqs', 'endpoint': 'arn:aws:sqs:...', 'healthy': True},
            {'name': 'audit-lambda', 'endpoint': 'arn:aws:lambda:...', 'healthy': False},
            {'name': 'analytics-sqs', 'endpoint': 'arn:aws:sqs:...', 'healthy': True},
            {'name': 'billing-webhook', 'endpoint': 'https://billing.example.com', 'healthy': False},
        ]

        event = {'event_type': 'order_created', 'order_id': 1}
        failed_deliveries = []

        self.stdout.write('Publishing event to SNS topic:')
        for sub in subscriptions:
            if sub['healthy']:
                self.stdout.write(self.style.SUCCESS(
                    f'  {sub["name"]}: delivered'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'  {sub["name"]}: DELIVERY FAILED (endpoint unhealthy)'
                ))
                failed_deliveries.append(sub['name'])

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: {len(failed_deliveries)} delivery failures - silently lost!'
        ))
        self.stdout.write(self.style.ERROR(
            '  - No dead-letter topic configured on SNS subscription\n'
            '  - Failed messages not stored anywhere\n'
            '  - No CloudWatch metric for NumberOfNotificationsFailed\n'
            '  - audit-lambda: compliance records missing\n'
            '  - billing-webhook: billing system out of sync'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Configure dead-letter queue on each SNS subscription')
        self.stdout.write('  - Monitor NumberOfNotificationsFailed CloudWatch metric')
        self.stdout.write('  - Set delivery retry policy per subscription')
        self.stdout.write('  - Use SQS subscriber (not HTTP) for critical subscriptions')
