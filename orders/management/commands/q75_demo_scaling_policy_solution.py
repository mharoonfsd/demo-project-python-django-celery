from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q75 SOLUTION: Use multiple metrics for ECS autoscaling. Primary: SQS
    queue depth. Secondary: memory utilization. Tertiary: CPU. Scale out
    when ANY metric exceeds threshold (OR logic).
    """
    help = 'Q75 Solution: Multi-metric ECS autoscaling policy'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q75 SOLUTION: Multi-metric autoscaling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q75-SOL-ORDER',
            customer_email='q75sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        THRESHOLDS = {
            'queue_depth': 100,    # scale out if queue > 100 messages
            'memory_pct': 75,      # scale out if memory > 75%
            'cpu_pct': 70,         # scale out if CPU > 70%
        }
        TARGET_MSGS_PER_TASK = 10
        MIN_TASKS = 1
        MAX_TASKS = 20

        def desired_tasks(queue_depth, memory_pct, cpu_pct, current_tasks):
            # Queue-depth driven scaling (primary)
            queue_based = max(MIN_TASKS, min(MAX_TASKS, queue_depth // TARGET_MSGS_PER_TASK))
            # Keep at least current tasks if memory/CPU are high
            if memory_pct > THRESHOLDS['memory_pct'] or cpu_pct > THRESHOLDS['cpu_pct']:
                return max(queue_based, current_tasks + 1)
            # Scale in slowly
            if queue_depth < THRESHOLDS['queue_depth']:
                return max(MIN_TASKS, current_tasks - 1)
            return queue_based

        snapshots = [
            {'t': 0, 'cpu': 15, 'mem': 40, 'queue': 10, 'tasks': 2},
            {'t': 1, 'cpu': 12, 'mem': 42, 'queue': 200, 'tasks': 2},
            {'t': 2, 'cpu': 14, 'mem': 45, 'queue': 800, 'tasks': 10},
            {'t': 3, 'cpu': 11, 'mem': 60, 'queue': 200, 'tasks': 20},
            {'t': 4, 'cpu': 13, 'mem': 50, 'queue': 50, 'tasks': 20},
        ]

        self.stdout.write('Multi-metric autoscaling simulation:')
        current_tasks = snapshots[0]['tasks']
        for snap in snapshots:
            new_desired = desired_tasks(snap['queue'], snap['mem'], snap['cpu'], current_tasks)
            trigger = []
            if snap['queue'] > THRESHOLDS['queue_depth']:
                trigger.append(f'queue={snap["queue"]}')
            if snap['mem'] > THRESHOLDS['memory_pct']:
                trigger.append(f'mem={snap["mem"]}%')
            if snap['cpu'] > THRESHOLDS['cpu_pct']:
                trigger.append(f'cpu={snap["cpu"]}%')

            trigger_str = ', '.join(trigger) if trigger else 'stable'
            action = f'-> {new_desired} tasks' if new_desired != current_tasks else '-> no change'
            self.stdout.write(self.style.SUCCESS(
                f'  t={snap["t"]}min: [{trigger_str}] {action}'
            ))
            current_tasks = new_desired

        self.stdout.write('\nAWS CDK / Terraform scaling config:')
        self.stdout.write('  # Step 1: Queue-depth target tracking')
        self.stdout.write('  scalable_target.scale_on_metric(')
        self.stdout.write('      metric=queue.metric_approximate_number_of_messages_visible(),')
        self.stdout.write('      target_value=10,  # 10 msgs per task')
        self.stdout.write('  )')
        self.stdout.write('  # Step 2: Memory step scaling (fallback)')
        self.stdout.write('  scalable_target.scale_on_metric(')
        self.stdout.write('      metric=service.metric_memory_utilization(),')
        self.stdout.write('      threshold=75, adjustment_type=ChangeInCapacity)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Primary scaling metric: SQS queue depth')
        self.stdout.write('  - Secondary: memory utilization (catches memory pressure)')
        self.stdout.write('  - CPU as tertiary (catches CPU-bound tasks)')
        self.stdout.write('  - Scale-in cooldown 5min, scale-out cooldown 30s')
