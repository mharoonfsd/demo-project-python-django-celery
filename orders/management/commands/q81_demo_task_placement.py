from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q81 PROBLEM: ECS task placement is random. Multiple tasks end up on the
    same EC2 instance. Instance failure takes down all tasks simultaneously,
    causing full service outage instead of graceful degradation.
    """
    help = 'Q81 Problem: Poor task placement - all tasks on same instance'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q81 PROBLEM: Random task placement - SPOF on single instance')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q81-ORDER',
            customer_email='q81@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate random placement: all 4 tasks ended up on instance-1
        cluster = {
            'instance-1': {'az': 'us-east-1a', 'tasks': ['task-1', 'task-2', 'task-3', 'task-4']},
            'instance-2': {'az': 'us-east-1b', 'tasks': []},
            'instance-3': {'az': 'us-east-1a', 'tasks': []},
        }

        self.stdout.write('Current task placement (random / unlucky):')
        for instance, data in cluster.items():
            task_str = ', '.join(data['tasks']) if data['tasks'] else '(no tasks)'
            self.stdout.write(f'  {instance} [{data["az"]}]: {task_str}')

        self.stdout.write(self.style.WARNING(
            '\n  All 4 tasks are on instance-1!'
        ))
        self.stdout.write('\nSimulating instance-1 failure:')
        self.stdout.write(self.style.ERROR(
            '  instance-1 terminated (EC2 spot interruption)\n'
            '  -> task-1 KILLED\n'
            '  -> task-2 KILLED\n'
            '  -> task-3 KILLED\n'
            '  -> task-4 KILLED\n'
            '  -> Service has 0 healthy tasks (COMPLETE OUTAGE)'
        ))
        self.stdout.write('  ECS replacements starting (takes 2-3 minutes)...')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Single instance failure = full outage'
            '\n  - Should have been 1-2 tasks per instance'
            '\n  - Should be spread across multiple AZs'
            '\n  - Spot instance interruption is a common scenario'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use spread placement: distinctInstance or spread by AZ')
        self.stdout.write('  - Tasks should span multiple AZs for HA')
        self.stdout.write('  - Use Fargate (no instances to manage) or spread strategy')
        self.stdout.write('  - Never run < 2 tasks in production (N+1 minimum)')
