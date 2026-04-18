from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q82 PROBLEM: ALB sticky sessions (session affinity) enabled. Once a client
    is assigned to a task, all its requests go to the same task. Heavy clients
    overload one task while others are idle. Scaling adds tasks but doesn't
    help existing clients.
    """
    help = 'Q82 Problem: Sticky sessions cause uneven ECS task load'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q82 PROBLEM: ALB sticky sessions cause load imbalance')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q82-ORDER',
            customer_email='q82@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Sticky sessions: clients permanently bound to one task
        tasks = {'task-1': 0, 'task-2': 0, 'task-3': 0}
        sticky_map = {}

        clients = [
            ('client-heavy', 80, 'task-1'),   # heavy client stuck on task-1
            ('client-medium', 15, 'task-2'),
            ('client-light', 5, 'task-3'),
        ]

        self.stdout.write('Request distribution with sticky sessions:')
        for client, rps, assigned_task in clients:
            sticky_map[client] = assigned_task
            tasks[assigned_task] += rps

        for task, rps in tasks.items():
            clients_on_task = [c for c, t in sticky_map.items() if t == task]
            bar = '#' * (rps // 2)
            self.stdout.write(f'  {task}: {rps:3d} rps [{bar}] <- {clients_on_task}')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: task-1 at 80 rps, task-3 at only 5 rps'
            '\n  - Adding a 4th ECS task does NOT help client-heavy'
            '\n  - client-heavy is stuck to task-1 via AWSALB cookie'
            '\n  - task-1 CPU/memory high; task-3 nearly idle'
            '\n  - Stateless services should NOT use sticky sessions'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Sticky sessions only needed for stateful apps (old monoliths)')
        self.stdout.write('  - Modern stateless services: store sessions in Redis/DynamoDB')
        self.stdout.write('  - With sticky sessions off, ALB round-robins evenly')
        self.stdout.write('  - Scaling adds capacity that ALL clients can use')
