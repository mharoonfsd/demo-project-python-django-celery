from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q70 SOLUTION: Configure dead-letter queues on SNS subscriptions.
    Monitor delivery failure metrics. Prefer SQS over HTTP for reliability.
    Set delivery retry policy with exponential backoff.
    """
    help = 'Q70 Solution: SNS delivery reliability - DLQ + monitoring'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q70 SOLUTION: SNS delivery with DLQ and monitoring')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q70-SOL-ORDER',
            customer_email='q70sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        subscriptions = [
            {'name': 'email-service-sqs', 'healthy': True, 'has_dlq': True},
            {'name': 'audit-lambda', 'healthy': False, 'has_dlq': True},
            {'name': 'analytics-sqs', 'healthy': True, 'has_dlq': True},
            {'name': 'billing-webhook', 'healthy': False, 'has_dlq': True},
        ]

        dlq_contents = []

        self.stdout.write('Publishing event (with DLQ configured on all subscriptions):')
        for sub in subscriptions:
            if sub['healthy']:
                self.stdout.write(self.style.SUCCESS(
                    f'  {sub["name"]}: delivered'
                ))
            else:
                # After retry policy exhausted, SNS routes to subscription DLQ
                dlq_contents.append(sub['name'])
                self.stdout.write(self.style.WARNING(
                    f'  {sub["name"]}: failed -> moved to subscription DLQ'
                ))

        self.stdout.write(f'\nDLQ contains {len(dlq_contents)} failed deliveries')
        if dlq_contents:
            self.stdout.write(self.style.WARNING('  CloudWatch alarm fires: SNS DLQ depth > 0'))
            self.stdout.write('  On-call engineer investigates...')
            for name in dlq_contents:
                self.stdout.write(f'    - Replaying {name} after fixing endpoint')

        self.stdout.write('\nSNS subscription DLQ configuration (boto3):')
        self.stdout.write('  sns.set_subscription_attributes(')
        self.stdout.write('      SubscriptionArn=sub_arn,')
        self.stdout.write('      AttributeName="RedrivePolicy",')
        self.stdout.write('      AttributeValue=json.dumps({')
        self.stdout.write('          "deadLetterTargetArn": dlq_arn')
        self.stdout.write('      })')
        self.stdout.write('  )')

        self.stdout.write('\nMonitoring:')
        self.stdout.write('  CloudWatch: NumberOfNotificationsFailed per subscription')
        self.stdout.write('  Alert threshold: > 0 for 5 minutes')
        self.stdout.write('  Action: PagerDuty -> investigate endpoint health')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set RedrivePolicy on every SNS subscription')
        self.stdout.write('  - Monitor NumberOfNotificationsFailed per subscription')
        self.stdout.write('  - Use SQS (not HTTP) for critical data (resilient to endpoint outages)')
        self.stdout.write('  - Build replay tooling: DLQ -> republish to SNS after fix')
