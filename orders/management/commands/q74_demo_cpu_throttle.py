from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q74 PROBLEM: ECS task CPU limit set too low. Task gets CPU throttled
    by cgroups — it wants more CPU but is rate-limited. Results in high
    latency and timeouts even though the host has available CPU.
    """
    help = 'Q74 Problem: ECS CPU throttling - high latency from CPU limits'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q74 PROBLEM: ECS CPU throttling - task starved of CPU')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q74-ORD-{i:03}',
                customer_email=f'q74user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        CPU_LIMIT_VCPU = 0.25  # 256 CPU units (0.25 vCPU)
        TASK_CPU_DEMAND = 0.8  # task wants 0.8 vCPU during processing

        self.stdout.write(f'ECS task CPU limit: {CPU_LIMIT_VCPU} vCPU ({int(CPU_LIMIT_VCPU * 1024)} CPU units)')
        self.stdout.write(f'Task CPU demand: {TASK_CPU_DEMAND} vCPU during processing')
        self.stdout.write('')

        throttle_ratio = max(0, (TASK_CPU_DEMAND - CPU_LIMIT_VCPU) / TASK_CPU_DEMAND)

        batches = [
            {'name': 'order_created event', 'expected_ms': 50},
            {'name': 'payment_captured event', 'expected_ms': 80},
            {'name': 'send_email_notification', 'expected_ms': 30},
        ]

        self.stdout.write('Processing times under CPU throttle:')
        for batch in batches:
            actual_ms = int(batch['expected_ms'] / (1 - throttle_ratio))
            self.stdout.write(self.style.ERROR(
                f'  {batch["name"]}: expected={batch["expected_ms"]}ms, '
                f'actual={actual_ms}ms (throttled by {throttle_ratio*100:.0f}%)'
            ))

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: CPU throttle factor = {throttle_ratio*100:.0f}%'
            '\n  - Task is waiting for CPU time it\'s allocated but not given'
            '\n  - Host may have 4 vCPU idle but task limited to 0.25'
            '\n  - Requests time out while CPU sits idle on host'
            '\n  - Misleading: host CPU low, task latency high'
        ))

        self.stdout.write('\nDiagnosis:')
        self.stdout.write('  - CloudWatch: CPUUtilization near 100% for the task')
        self.stdout.write('  - Check: container_cpu_throttled_periods metric')
        self.stdout.write('  - host CPU low + task CPU 100% = CPU limit too low')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - CPU limit 256 units (0.25 vCPU) is common misconfiguration')
        self.stdout.write('  - Measure actual CPU usage during load test')
        self.stdout.write('  - Set CPU limit to 1.5-2x measured average CPU usage')
        self.stdout.write('  - Use cpu (hard limit) or leave it unset for burstable')
