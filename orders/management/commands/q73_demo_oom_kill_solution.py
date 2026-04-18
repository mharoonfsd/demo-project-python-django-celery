from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q73 SOLUTION: Profile memory under realistic load. Set memory limit 2x
    peak measured. Use memoryReservation + memory in task definition.
    Alert at 80% utilization before OOM occurs.
    """
    help = 'Q73 Solution: Right-size ECS memory limits and add alerting'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q73 SOLUTION: Proper ECS memory configuration')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q73-SOL-{i:03}',
                customer_email=f'q73sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        MEASURED_PEAK_MB = 230
        SAFETY_FACTOR = 2.0
        MEMORY_HARD_LIMIT = int(MEASURED_PEAK_MB * SAFETY_FACTOR)  # 460MB
        MEMORY_RESERVATION = int(MEASURED_PEAK_MB * 1.2)           # 276MB (soft limit)
        ALERT_THRESHOLD_PCT = 80

        self.stdout.write(f'Measured peak usage: {MEASURED_PEAK_MB}MB')
        self.stdout.write(f'Recommended hard limit (2x): {MEMORY_HARD_LIMIT}MB')
        self.stdout.write(f'Recommended reservation (1.2x): {MEMORY_RESERVATION}MB')
        self.stdout.write(f'Alert threshold: {ALERT_THRESHOLD_PCT}%')
        self.stdout.write('')

        simulated_usage = [80, 120, 180, 230, 240, 250]
        self.stdout.write('Memory usage with proper limits:')
        for i, usage in enumerate(simulated_usage):
            t = i * 10
            pct = usage / MEMORY_HARD_LIMIT * 100
            if pct >= ALERT_THRESHOLD_PCT:
                self.stdout.write(self.style.WARNING(
                    f'  t={t}s: {usage}MB / {MEMORY_HARD_LIMIT}MB ({pct:.0f}%) <- ALERT: investigate'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  t={t}s: {usage}MB / {MEMORY_HARD_LIMIT}MB ({pct:.0f}%) OK'
                ))

        self.stdout.write('\nECS task definition JSON:')
        self.stdout.write('  {')
        self.stdout.write(f'    "memory": {MEMORY_HARD_LIMIT},       // hard limit (OOM if exceeded)')
        self.stdout.write(f'    "memoryReservation": {MEMORY_RESERVATION}  // soft limit (guaranteed)')
        self.stdout.write('  }')

        self.stdout.write('\nMemory profiling commands:')
        self.stdout.write('  # Python memory profiler')
        self.stdout.write('  from memory_profiler import profile')
        self.stdout.write('  @profile')
        self.stdout.write('  def process_batch(): ...')
        self.stdout.write('')
        self.stdout.write('  # Docker stats during load test')
        self.stdout.write('  docker stats --format "{{.MemUsage}}"')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always load test and measure peak memory before setting limits')
        self.stdout.write('  - Hard limit = 2x measured peak (safety margin)')
        self.stdout.write('  - Alert at 80% of hard limit -> time to investigate')
        self.stdout.write('  - memoryReservation ensures scheduler allocates enough capacity')
