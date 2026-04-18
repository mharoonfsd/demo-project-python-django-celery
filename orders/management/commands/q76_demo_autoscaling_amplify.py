from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q76 PROBLEM: ECS autoscaling amplifies the problem. Scaling out during
    a traffic spike adds many tasks simultaneously. Each new task opens DB
    connections on startup, overwhelming the DB when it's already stressed.
    """
    help = 'Q76 Problem: Autoscaling amplifies DB load during spike'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q76 PROBLEM: Autoscaling amplifies the problem')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q76-ORDER',
            customer_email='q76@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        CONNECTIONS_PER_TASK = 10
        DB_MAX_CONNECTIONS = 100
        SCALE_STEP = 10   # scale out 10 tasks at once

        self.stdout.write(f'ECS scaling config:')
        self.stdout.write(f'  Scale step: +{SCALE_STEP} tasks per scale event')
        self.stdout.write(f'  Connections per task: {CONNECTIONS_PER_TASK}')
        self.stdout.write(f'  DB max connections: {DB_MAX_CONNECTIONS}')
        self.stdout.write('')

        tasks = 2
        db_connections = tasks * CONNECTIONS_PER_TASK

        self.stdout.write('Scale-out event during traffic spike:')
        self.stdout.write(f'  Before: {tasks} tasks = {db_connections} DB connections')

        tasks += SCALE_STEP
        db_connections = tasks * CONNECTIONS_PER_TASK
        connection_spike = db_connections - (2 * CONNECTIONS_PER_TASK)

        self.stdout.write(self.style.ERROR(
            f'  After scale-out: {tasks} tasks = {db_connections} DB connections'
        ))
        if db_connections > DB_MAX_CONNECTIONS:
            self.stdout.write(self.style.ERROR(
                f'  OVER DB limit by {db_connections - DB_MAX_CONNECTIONS} connections!'
                f'\n  All {tasks} tasks fighting for {DB_MAX_CONNECTIONS} connections'
                f'\n  DB overwhelmed at the exact moment it needs to scale!'
            ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Scaling paradox\n'
            '  1. Traffic spike -> DB slow\n'
            '  2. Autoscaler adds 10 tasks to handle load\n'
            '  3. 10 new tasks each open 10 DB connections\n'
            '  4. DB connection pool exhausted\n'
            '  5. DB even slower -> more timeouts -> more queue depth\n'
            '  6. Autoscaler adds MORE tasks\n'
            '  7. Total collapse'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Large scale steps create connection storms')
        self.stdout.write('  - Use RDS Proxy to decouple connections from task count')
        self.stdout.write('  - Scale in smaller steps with longer cooldowns')
        self.stdout.write('  - Cap max tasks below DB_MAX_CONNECTIONS / CONNS_PER_TASK')
