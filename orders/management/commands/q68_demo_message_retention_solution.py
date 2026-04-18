from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q68 SOLUTION: Set MessageRetentionPeriod to 14 days (maximum). Combine
    with DLQ that also has 14-day retention. Alert when oldest message age
    exceeds a threshold, giving engineers time to fix bugs before data loss.
    """
    help = 'Q68 Solution: Maximize message retention and alert on age'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q68 SOLUTION: 14-day retention + age alerting')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q68-SOL-ORDER',
            customer_email='q68sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        MAX_RETENTION_DAYS = 14
        BUG_DISCOVERED_DAY = 3
        BUG_FIXED_DAY = 5
        ALERT_THRESHOLD_HOURS = 12

        self.stdout.write(f'Recommended queue config:')
        self.stdout.write(f'  MessageRetentionPeriod = {MAX_RETENTION_DAYS} days (maximum)')
        self.stdout.write(f'  DLQ MessageRetentionPeriod = {MAX_RETENTION_DAYS} days')
        self.stdout.write(f'  Age alert threshold = {ALERT_THRESHOLD_HOURS} hours')
        self.stdout.write('')

        timeline = [
            (0, 'Bug deployed - consumer starts failing'),
            (0.5, f'ALERT FIRES: oldest message > {ALERT_THRESHOLD_HOURS}h — page engineer'),
            (BUG_DISCOVERED_DAY, 'Engineer investigates (alerted early)'),
            (BUG_FIXED_DAY, 'Bug fixed - replay messages from DLQ'),
            (MAX_RETENTION_DAYS, 'Messages would expire (but bug was fixed 9 days ago)'),
        ]

        for day, event in timeline:
            if 'ALERT' in event:
                self.stdout.write(self.style.WARNING(f'  Day {day:.1f}: {event}'))
            elif 'fixed' in event or 'replay' in event:
                self.stdout.write(self.style.SUCCESS(f'  Day {day}: {event}'))
            else:
                self.stdout.write(f'  Day {day}: {event}')

        self.stdout.write(self.style.SUCCESS(
            '\nResult: No data loss - messages available for 14 days'
        ))

        self.stdout.write('\nboto3 configuration:')
        self.stdout.write('  sqs.set_queue_attributes(')
        self.stdout.write('      QueueUrl=queue_url,')
        self.stdout.write('      Attributes={')
        self.stdout.write('          "MessageRetentionPeriod": str(14 * 24 * 3600)  # 14 days')
        self.stdout.write('      }')
        self.stdout.write('  )')

        self.stdout.write('\nCloudWatch alarm:')
        self.stdout.write('  Metric: ApproximateAgeOfOldestMessage')
        self.stdout.write('  Threshold: 43200  # 12 hours in seconds')
        self.stdout.write('  Action: SNS -> PagerDuty')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always set retention to 14 days for critical queues')
        self.stdout.write('  - Alert EARLY on message age (12h gives time to react)')
        self.stdout.write('  - DLQ also needs 14-day retention (independent setting)')
        self.stdout.write('  - Build DLQ replay tooling BEFORE you need it')
