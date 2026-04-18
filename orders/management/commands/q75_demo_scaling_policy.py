from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q75 PROBLEM: ECS autoscaling policy based only on CPU utilization.
    The service scales out when CPU is high, but the real bottleneck is
    queue depth or memory. CPU-only scaling misses the actual problem.
    """
    help = 'Q75 Problem: CPU-only autoscaling policy misses real bottleneck'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q75 PROBLEM: CPU-only autoscaling misses queue backlog')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q75-ORDER',
            customer_email='q75@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Scenario: IO-bound task - waiting on slow external API
        # CPU is LOW (task is waiting), but queue is growing
        metrics_timeline = [
            {'t': 0, 'cpu_pct': 15, 'queue_depth': 10,   'tasks': 2},
            {'t': 1, 'cpu_pct': 12, 'queue_depth': 200,  'tasks': 2},
            {'t': 2, 'cpu_pct': 14, 'queue_depth': 800,  'tasks': 2},
            {'t': 3, 'cpu_pct': 11, 'queue_depth': 2000, 'tasks': 2},
            {'t': 4, 'cpu_pct': 13, 'queue_depth': 5000, 'tasks': 2},
        ]

        SCALE_OUT_CPU_THRESHOLD = 70
        self.stdout.write(f'Autoscaling policy: scale out when CPU > {SCALE_OUT_CPU_THRESHOLD}%')
        self.stdout.write('')
        self.stdout.write('System state over time:')

        for snap in metrics_timeline:
            cpu_trigger = snap['cpu_pct'] > SCALE_OUT_CPU_THRESHOLD
            scale_note = ' -> SCALE OUT' if cpu_trigger else ' -> no scaling (CPU low)'
            self.stdout.write(
                f'  t={snap["t"]}min: cpu={snap["cpu_pct"]}%, '
                f'queue={snap["queue_depth"]}, tasks={snap["tasks"]}{scale_note}'
            )
            if snap['queue_depth'] > 1000:
                self.stdout.write(self.style.ERROR(
                    f'    PROBLEM: Queue growing rapidly but autoscaler does nothing!'
                ))

        self.stdout.write(self.style.ERROR(
            '\nROOT CAUSE:\n'
            '  - Task is IO-bound (waiting for external API)\n'
            '  - CPU stays low while task waits\n'
            '  - CPU-only policy never triggers scale-out\n'
            '  - Queue backlog grows to 5000 messages'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - CPU is a lagging indicator for IO-bound workloads')
        self.stdout.write('  - Scale on SQS queue depth (primary metric)')
        self.stdout.write('  - Add memory utilization as secondary metric')
        self.stdout.write('  - Use multiple metrics with OR logic for scale-out')
