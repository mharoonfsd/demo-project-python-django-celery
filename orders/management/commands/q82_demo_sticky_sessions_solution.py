from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q82 SOLUTION: Disable ALB sticky sessions. Store session data in Redis
    or DynamoDB (external store). With stateless tasks, ALB distributes load
    evenly and new tasks immediately absorb traffic.
    """
    help = 'Q82 Solution: Stateless tasks with external session store'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q82 SOLUTION: Stateless tasks + external session store')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q82-SOL-ORDER',
            customer_email='q82sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Without sticky sessions: ALB distributes evenly
        tasks = {'task-1': 0, 'task-2': 0, 'task-3': 0}
        total_rps = 100
        task_list = list(tasks.keys())

        self.stdout.write('Request distribution without sticky sessions (round-robin):')
        for i in range(total_rps):
            task = task_list[i % len(task_list)]
            tasks[task] += 1

        for task, rps in tasks.items():
            bar = '#' * (rps // 2)
            self.stdout.write(self.style.SUCCESS(
                f'  {task}: {rps:3d} rps [{bar}]'
            ))

        self.stdout.write('\nScaling out: add task-4')
        tasks['task-4'] = 0
        task_list = list(tasks.keys())
        for task in tasks:
            tasks[task] = 0
        for i in range(total_rps):
            task = task_list[i % len(task_list)]
            tasks[task] += 1
        for task, rps in tasks.items():
            bar = '#' * (rps // 2)
            self.stdout.write(self.style.SUCCESS(
                f'  {task}: {rps:3d} rps [{bar}]'
            ))
        self.stdout.write(self.style.SUCCESS('  New task immediately gets its share of traffic'))

        self.stdout.write('\nExternal session store (Django settings):')
        self.stdout.write('  SESSION_ENGINE = "django.contrib.sessions.backends.cache"')
        self.stdout.write('  CACHES = {')
        self.stdout.write('      "default": {')
        self.stdout.write('          "BACKEND": "django_redis.cache.RedisCache",')
        self.stdout.write('          "LOCATION": "redis://elasticache-cluster:6379/1",')
        self.stdout.write('      }')
        self.stdout.write('  }')

        self.stdout.write('\nALB target group (disable stickiness):')
        self.stdout.write('  Stickiness: Disabled (default for new target groups)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Store sessions in Redis/ElastiCache, not in-memory')
        self.stdout.write('  - Stateless tasks: any task can serve any request')
        self.stdout.write('  - ALB round-robin distributes load evenly')
        self.stdout.write('  - New tasks immediately receive traffic on scale-out')
