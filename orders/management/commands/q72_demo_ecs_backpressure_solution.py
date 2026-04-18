from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q72 SOLUTION: Use SQS queue depth as the primary autoscaling metric.
    Scale ECS tasks based on ApproximateNumberOfMessages / target messages-per-task.
    Implement producer backpressure when queue exceeds threshold.
    """
    help = 'Q72 Solution: ECS autoscaling on SQS queue depth'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q72 SOLUTION: Queue-depth driven ECS autoscaling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q72-SOL-ORDER',
            customer_email='q72sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        TARGET_MSGS_PER_TASK = 10
        MIN_TASKS = 1
        MAX_TASKS = 50
        process_rate_per_task = 10  # msg/s per ECS task
        input_rate = 100
        backpressure_threshold = 500

        def desired_tasks(queue_depth):
            desired = max(MIN_TASKS, min(MAX_TASKS,
                round(queue_depth / TARGET_MSGS_PER_TASK)))
            return desired

        def producer_rate(queue_depth):
            if queue_depth > backpressure_threshold:
                return input_rate * 0.3  # throttle to 30%
            return input_rate

        current_tasks = 1
        queue_depth = 0

        self.stdout.write('Queue depth + autoscaling simulation:')
        for t in range(1, 9):
            actual_input = producer_rate(queue_depth)
            actual_process = current_tasks * process_rate_per_task
            queue_depth = max(0, queue_depth + actual_input - actual_process)

            new_desired = desired_tasks(queue_depth)
            scale_action = ''
            if new_desired > current_tasks:
                scale_action = f' -> scaling OUT to {new_desired} tasks'
            elif new_desired < current_tasks:
                scale_action = f' -> scaling IN to {new_desired} tasks'
            current_tasks = new_desired

            throttle_note = ' [producer throttled]' if actual_input < input_rate else ''
            self.stdout.write(
                f'  t={t}s: depth={int(queue_depth)}, tasks={current_tasks}'
                f'{throttle_note}{scale_action}'
            )

        self.stdout.write('\nECS Application Auto Scaling config:')
        self.stdout.write('  Metric: SQS ApproximateNumberOfMessages')
        self.stdout.write('  Target: queue_depth / desired_tasks_count = 10')
        self.stdout.write('  Scale-out cooldown: 30s')
        self.stdout.write('  Scale-in cooldown: 300s (avoid thrashing)')

        self.stdout.write('\nProducer backpressure pattern:')
        self.stdout.write('  # Before publishing, check queue depth')
        self.stdout.write('  depth = sqs.get_queue_attributes(...)["ApproximateNumberOfMessages"]')
        self.stdout.write('  if int(depth) > BACKPRESSURE_THRESHOLD:')
        self.stdout.write('      rate_limiter.throttle()  # slow down or pause')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Scale on queue depth, not CPU (CPU is a lagging indicator)')
        self.stdout.write('  - Formula: desired_tasks = queue_depth / target_messages_per_task')
        self.stdout.write('  - Implement producer backpressure at high queue depth')
        self.stdout.write('  - Scale-in cooldown >> scale-out cooldown to avoid thrashing')
