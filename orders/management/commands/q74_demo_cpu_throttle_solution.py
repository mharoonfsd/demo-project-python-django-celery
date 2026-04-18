from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q74 SOLUTION: Profile CPU usage under realistic load. Set CPU limit 2x
    average measured usage. Use Fargate CPU/memory combinations. Monitor
    ThrottledPeriods metric to detect CPU starvation.
    """
    help = 'Q74 Solution: Right-size ECS CPU limits based on profiling'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q74 SOLUTION: Right-sized CPU limits')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q74-SOL-{i:03}',
                customer_email=f'q74sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        MEASURED_AVG_CPU_VCPU = 0.4
        MEASURED_PEAK_CPU_VCPU = 0.7
        RECOMMENDED_LIMIT = 1.0  # 1 vCPU (Fargate valid: 0.25, 0.5, 1, 2, 4)

        self.stdout.write(f'Profiling results:')
        self.stdout.write(f'  Average CPU usage: {MEASURED_AVG_CPU_VCPU} vCPU')
        self.stdout.write(f'  Peak CPU usage: {MEASURED_PEAK_CPU_VCPU} vCPU')
        self.stdout.write(f'  Recommended limit: {RECOMMENDED_LIMIT} vCPU (next Fargate tier)')
        self.stdout.write('')

        batches = [
            {'name': 'order_created event', 'expected_ms': 50},
            {'name': 'payment_captured event', 'expected_ms': 80},
            {'name': 'send_email_notification', 'expected_ms': 30},
        ]

        self.stdout.write('Processing times with correct CPU limit:')
        for batch in batches:
            self.stdout.write(self.style.SUCCESS(
                f'  {batch["name"]}: {batch["expected_ms"]}ms (no throttle)'
            ))

        self.stdout.write('\nFargate CPU/Memory valid combinations:')
        combos = [
            ('256 (.25 vCPU)', '512MB - 2GB'),
            ('512 (.5 vCPU)', '1GB - 4GB'),
            ('1024 (1 vCPU)', '2GB - 8GB'),
            ('2048 (2 vCPU)', '4GB - 16GB'),
            ('4096 (4 vCPU)', '8GB - 30GB'),
        ]
        for cpu, mem in combos:
            marker = ' <- recommended' if '1024' in cpu else ''
            self.stdout.write(f'  CPU: {cpu}, Memory: {mem}{marker}')

        self.stdout.write('\nMonitoring CPU throttle:')
        self.stdout.write('  CloudWatch metric: container_cpu_throttled_periods_total')
        self.stdout.write('  Alert if throttled_periods / total_periods > 10%')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Load test and measure CPU at realistic concurrency')
        self.stdout.write('  - Set CPU limit to next Fargate tier above measured peak')
        self.stdout.write('  - Monitor throttled_periods — if > 0, limit is too low')
        self.stdout.write('  - More tasks with less CPU each is often better than fewer big tasks')
