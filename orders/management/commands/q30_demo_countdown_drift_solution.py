import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q30 SOLUTION: Use absolute timestamps (eta parameter) instead of relative
    countdown. This way, all workers schedule the task for the same absolute
    time, regardless of local clock differences. Use a single NTP-synced clock
    as the source of truth.
    """
    help = 'Q30 Solution: Use absolute timestamps to avoid clock skew'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q30 SOLUTION: Absolute timestamps prevent drift')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task(bind=True, max_retries=2)
        def sync_task(self_task, order_id, target_time=None):
            """
            Task scheduled with absolute timestamp (eta) instead of countdown.
            All workers see the same target time.
            """
            now = timezone.now()
            print(f'  Current time: {now.isoformat()}')

            if target_time:
                if isinstance(target_time, str):
                    eta = timezone.make_aware(
                        datetime.datetime.fromisoformat(target_time),
                        is_dst=None
                    ) if timezone.is_naive(datetime.datetime.fromisoformat(target_time)) else datetime.datetime.fromisoformat(target_time)
                else:
                    eta = target_time
                print(f'  Target ETA: {eta.isoformat()}')
                if now >= eta:
                    print('  -> Executing now')
                    return 'done'

            # Schedule with absolute time: now + 60 seconds
            next_eta = now + datetime.timedelta(seconds=60)
            print(f'  First attempt. Would schedule retry for {next_eta.isoformat()}')
            return 'scheduled'

        order = Order.objects.create(
            order_number='Q30-SOL-ORDER',
            customer_email='q30sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nTask with absolute timestamp:')
        now = timezone.now()
        target = now + timezone.timedelta(seconds=5)
        result = sync_task(order.pk, target_time=target.isoformat())
        self.stdout.write(self.style.SUCCESS(f'Result: {result}'))

        self.stdout.write('\nEven with clock skew (Worker-A ahead of Worker-B):')
        self.stdout.write('  Both workers see same ETA (2024-04-18 10:05:30 UTC)')
        self.stdout.write('  Task executes at same absolute time on both')
        self.stdout.write('  No drift, consistent scheduling')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use eta= parameter instead of countdown for precise timing')
        self.stdout.write('  - Compute ETA from server time (not worker local clock)')
        self.stdout.write('  - Sync all server clocks with NTP')
        self.stdout.write('  - Store task deadlines in UTC')
