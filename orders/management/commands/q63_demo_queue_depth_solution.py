from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q63 SOLUTION: Set CloudWatch alarms on SQS metrics. Use
    ApproximateAgeOfOldestMessage as primary SLA alert. Implement
    auto-scaling consumers based on queue depth.
    """
    help = 'Q63 Solution: SQS monitoring with CloudWatch alarms'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q63 SOLUTION: SQS queue monitoring setup')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q63-SOL-ORDER',
            customer_email='q63sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate monitoring evaluation
        metrics = {
            'ApproximateNumberOfMessages': 3200,
            'ApproximateAgeOfOldestMessage': 7200,  # seconds (2 hours)
            'NumberOfMessagesSent': 50,
            'NumberOfMessagesDeleted': 5,
        }

        alarms = [
            {
                'name': 'QueueDepthHigh',
                'metric': 'ApproximateNumberOfMessages',
                'threshold': 1000,
                'action': 'Scale up consumers',
            },
            {
                'name': 'OldestMessageAge',
                'metric': 'ApproximateAgeOfOldestMessage',
                'threshold': 1800,  # 30 minutes in seconds
                'action': 'Page on-call engineer',
            },
            {
                'name': 'DLQNotEmpty',
                'metric': 'ApproximateNumberOfMessages',
                'threshold': 0,
                'action': 'Alert development team',
            },
        ]

        self.stdout.write('Current queue metrics:')
        for k, v in metrics.items():
            self.stdout.write(f'  {k}: {v:,}')

        self.stdout.write('\nAlarm evaluation:')
        for alarm in alarms:
            metric_value = metrics.get(alarm['metric'], 0)
            firing = metric_value > alarm['threshold']
            if firing:
                self.stdout.write(self.style.ERROR(
                    f'  ALARM FIRING: {alarm["name"]} -> {alarm["action"]}'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  OK: {alarm["name"]}'
                ))

        self.stdout.write('\nCloudWatch Alarm (AWS CDK):')
        self.stdout.write('  cloudwatch.Alarm(')
        self.stdout.write('      metric=queue.metric_approximate_age_of_oldest_message(),')
        self.stdout.write('      threshold=1800,')
        self.stdout.write('      evaluation_periods=1,')
        self.stdout.write('      alarm_actions=[sns_topic],')
        self.stdout.write('  )')

        self.stdout.write('\nAuto-scaling based on queue depth:')
        self.stdout.write('  Target: 10 messages per consumer instance')
        self.stdout.write('  At 3200 messages -> scale to 320 consumers')
        self.stdout.write('  ECS Application Auto Scaling with SQS metric')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Alert on ApproximateAgeOfOldestMessage (best SLA metric)')
        self.stdout.write('  - Alert on DLQ depth > 0 (poison messages)')
        self.stdout.write('  - Auto-scale consumers on ApproximateNumberOfMessages')
        self.stdout.write('  - Set retention period to at least 4x your SLA time')
