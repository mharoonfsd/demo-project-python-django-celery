from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q63 PROBLEM: No monitoring on SQS queue depth. Queue fills up silently,
    messages age out, consumers fall behind, and the business experiences
    delayed processing without any alert or visibility.
    """
    help = 'Q63 Problem: No queue depth monitoring - silent backlog buildup'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q63 PROBLEM: No SQS queue depth monitoring')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q63-ORD-{i:03}',
                customer_email=f'q63user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Simulate growing queue with no alerts
        queue_snapshots = [
            {'time': '09:00', 'depth': 10, 'oldest_age_min': 1},
            {'time': '09:30', 'depth': 150, 'oldest_age_min': 15},
            {'time': '10:00', 'depth': 800, 'oldest_age_min': 45},
            {'time': '10:30', 'depth': 3200, 'oldest_age_min': 120},
            {'time': '11:00', 'depth': 7500, 'oldest_age_min': 240},
        ]

        MESSAGE_RETENTION_SECONDS = 4 * 3600  # 4 hours default
        SLA_MAX_AGE_MIN = 30  # orders must be processed within 30 min

        self.stdout.write('Queue state over time (no monitoring, no alerts):')
        for snap in queue_snapshots:
            age_violation = snap['oldest_age_min'] > SLA_MAX_AGE_MIN
            status = '  [VIOLATED SLA]' if age_violation else ''
            self.stdout.write(
                f'  {snap["time"]}: depth={snap["depth"]:,} '
                f'oldest={snap["oldest_age_min"]}min{status}'
            )

        self.stdout.write('')
        self.stdout.write(self.style.ERROR(
            'PROBLEM: Nobody noticed until 11:00\n'
            '  - 7,500 unprocessed messages\n'
            '  - Oldest message: 4 hours old (will expire soon!)\n'
            '  - Orders delayed, customers angry\n'
            '  - No alert fired, no engineer paged\n'
            '  - Consumer was down since 09:00 - nobody knew'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Monitor ApproximateNumberOfMessages in CloudWatch')
        self.stdout.write('  - Alert on ApproximateAgeOfOldestMessage > SLA threshold')
        self.stdout.write('  - Alert on DLQ depth > 0')
        self.stdout.write('  - Set up auto-scaling based on queue depth')
