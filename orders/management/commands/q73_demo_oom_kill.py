from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q73 PROBLEM: ECS task memory limit set too low. Task gets OOM-killed
    by the container runtime without warning. Process dies immediately,
    no graceful shutdown, no logging of what caused the OOM.
    """
    help = 'Q73 Problem: ECS container OOM kill - task dies silently'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q73 PROBLEM: ECS container OOM kill')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q73-ORD-{i:03}',
                customer_email=f'q73user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        MEMORY_LIMIT_MB = 256
        simulated_usage = [80, 120, 180, 230, 260, 290]  # MB over time

        self.stdout.write(f'ECS task definition: memory={MEMORY_LIMIT_MB}MB')
        self.stdout.write('')
        self.stdout.write('Memory usage over time:')

        for i, usage in enumerate(simulated_usage):
            t = i * 10
            if usage > MEMORY_LIMIT_MB:
                self.stdout.write(self.style.ERROR(
                    f'  t={t}s: {usage}MB / {MEMORY_LIMIT_MB}MB — OOM KILL!'
                    f'\n    Container killed by cgroups (exit code 137)'
                    f'\n    No SIGTERM, no graceful shutdown, no cleanup'
                ))
                break
            pct = usage / MEMORY_LIMIT_MB * 100
            self.stdout.write(f'  t={t}s: {usage}MB / {MEMORY_LIMIT_MB}MB ({pct:.0f}%)')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: OOM kill causes:\n'
            '  - Process dies without warning (exit code 137)\n'
            '  - In-flight messages not acknowledged (redelivered)\n'
            '  - No log output showing what allocated the memory\n'
            '  - ECS auto-restarts task -> OOM again if load unchanged\n'
            '  - Restart loop: task keeps dying under load'
        ))

        self.stdout.write('\nHow to diagnose OOM kill:')
        self.stdout.write('  - ECS task exit code 137 = OOM kill')
        self.stdout.write('  - CloudWatch: MemoryUtilization metric near 100%')
        self.stdout.write('  - ECS task stopped reason: "OutOfMemoryError"')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Set memory limit 2x your measured peak usage')
        self.stdout.write('  - Add memory-based CloudWatch alarm at 80%')
        self.stdout.write('  - Profile memory usage under realistic load')
        self.stdout.write('  - Use memoryReservation (soft limit) + memory (hard limit)')
