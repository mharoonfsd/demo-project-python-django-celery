from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q81 SOLUTION: Use spread placement strategy across AZs and instances.
    Combine with minimum task count of 2+ to ensure HA. Use Fargate for
    automatic spread across AZs without managing instances.
    """
    help = 'Q81 Solution: Spread placement across AZs and instances'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q81 SOLUTION: Spread task placement for high availability')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q81-SOL-ORDER',
            customer_email='q81sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Spread placement: 1 task per AZ and per instance
        cluster_spread = {
            'instance-1': {'az': 'us-east-1a', 'tasks': ['task-1']},
            'instance-2': {'az': 'us-east-1b', 'tasks': ['task-2']},
            'instance-3': {'az': 'us-east-1c', 'tasks': ['task-3']},
            'instance-4': {'az': 'us-east-1a', 'tasks': ['task-4']},
        }

        self.stdout.write('Task placement with spread strategy:')
        for instance, data in cluster_spread.items():
            task_str = ', '.join(data['tasks'])
            self.stdout.write(self.style.SUCCESS(
                f'  {instance} [{data["az"]}]: {task_str}'
            ))

        self.stdout.write('\nSimulating instance-1 failure:')
        surviving = {k: v for k, v in cluster_spread.items() if k != 'instance-1'}
        surviving_tasks = [t for v in surviving.values() for t in v['tasks']]
        self.stdout.write(self.style.WARNING('  instance-1 terminated'))
        self.stdout.write(self.style.SUCCESS(
            f'  Still healthy: {surviving_tasks} ({len(surviving_tasks)}/4 tasks)'
            f'\n  Service continues operating at 75% capacity'
            f'\n  ECS replaces task-1 on remaining instances'
        ))

        self.stdout.write('\nECS placement strategies (JSON):')
        self.stdout.write('  // Spread across AZs first, then instances')
        self.stdout.write('  "placementStrategy": [')
        self.stdout.write('    {"type": "spread", "field": "attribute:ecs.availability-zone"},')
        self.stdout.write('    {"type": "spread", "field": "instanceId"}')
        self.stdout.write('  ]')

        self.stdout.write('\nFargate: automatic AZ spread (no placement strategy needed)')
        self.stdout.write('  - Fargate schedules tasks across AZs automatically')
        self.stdout.write('  - No instances to manage or spread manually')
        self.stdout.write('  - Best practice for new services')

        self.stdout.write('\nMinimum task count for HA:')
        self.stdout.write('  - Minimum 2 tasks (N+1 minimum for any production service)')
        self.stdout.write('  - Minimum 3 tasks to tolerate 1 failure while scaling')
        self.stdout.write('  - Circuit breaker + health checks handle partial degradation')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always spread across AZs: tolerate single-AZ failure')
        self.stdout.write('  - Spread across instances: tolerate single-host failure')
        self.stdout.write('  - Use Fargate for automatic spread without configuration')
        self.stdout.write('  - Minimum 2 tasks in production always (never 1)')
