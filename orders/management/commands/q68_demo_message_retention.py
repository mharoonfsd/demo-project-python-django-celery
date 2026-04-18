from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q68 PROBLEM: SQS message retention set to default (4 days). Messages
    that fail processing can expire and be lost before the bug is fixed.
    No alerting on message age means data silently disappears.
    """
    help = 'Q68 Problem: Short message retention - messages expire silently'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q68 PROBLEM: Message retention too short - silent data loss')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q68-ORDER',
            customer_email='q68@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        DEFAULT_RETENTION_DAYS = 4
        BUG_DISCOVERED_DAY = 3
        BUG_FIXED_DAY = 5

        self.stdout.write(f'Queue config:')
        self.stdout.write(f'  MessageRetentionPeriod = {DEFAULT_RETENTION_DAYS} days (default)')
        self.stdout.write(f'  Queue has been accumulating failed messages')
        self.stdout.write('')

        timeline = [
            (0, 'Bug deployed - consumer starts failing'),
            (BUG_DISCOVERED_DAY, f'Bug discovered at day {BUG_DISCOVERED_DAY}'),
            (DEFAULT_RETENTION_DAYS, f'Messages expire at day {DEFAULT_RETENTION_DAYS}'),
            (BUG_FIXED_DAY, f'Bug fixed at day {BUG_FIXED_DAY} - TOO LATE'),
        ]

        for day, event in timeline:
            if day >= DEFAULT_RETENTION_DAYS and 'expire' in event:
                self.stdout.write(self.style.ERROR(f'  Day {day}: {event}'))
            elif day == BUG_FIXED_DAY:
                self.stdout.write(self.style.ERROR(f'  Day {day}: {event}'))
            else:
                self.stdout.write(f'  Day {day}: {event}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: 4 days of orders permanently lost\n'
            '  - Messages expired before bug was fixed\n'
            '  - No alert on ApproximateAgeOfOldestMessage\n'
            '  - No DLQ to hold messages longer\n'
            '  - Data unrecoverable - customer orders lost'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Default SQS retention = 4 days (max = 14 days)')
        self.stdout.write('  - Set retention to 14 days for critical queues')
        self.stdout.write('  - DLQ holds messages separately (also 14 day max)')
        self.stdout.write('  - Alert when oldest message age > 50% of retention period')
