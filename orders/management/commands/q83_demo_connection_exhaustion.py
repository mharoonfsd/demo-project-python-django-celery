from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q83 PROBLEM: 50 ECS tasks, each opens 10 DB connections = 500 connections.
    RDS max_connections=100. New tasks fail to connect. Existing tasks see
    intermittent connection errors. DB CPU spikes just managing connections.
    """
    help = 'Q83 Problem: DB connection exhaustion with many ECS tasks'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q83 PROBLEM: DB connection exhaustion - too many ECS tasks')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q83-ORDER',
            customer_email='q83@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        RDS_MAX_CONNECTIONS = 100
        CONNECTIONS_PER_TASK = 10

        self.stdout.write(f'RDS max_connections: {RDS_MAX_CONNECTIONS}')
        self.stdout.write(f'Connections per ECS task: {CONNECTIONS_PER_TASK}')
        self.stdout.write(f'Max safe task count: {RDS_MAX_CONNECTIONS // CONNECTIONS_PER_TASK}')
        self.stdout.write('')
        self.stdout.write('Scaling event (traffic spike):')

        for num_tasks in [5, 10, 15, 20, 50]:
            total_conns = num_tasks * CONNECTIONS_PER_TASK
            if total_conns > RDS_MAX_CONNECTIONS:
                self.stdout.write(self.style.ERROR(
                    f'  {num_tasks:2d} tasks × {CONNECTIONS_PER_TASK} conns = {total_conns} '
                    f'> {RDS_MAX_CONNECTIONS} MAX -> PGCONNECTIONERROR'
                ))
            else:
                self.stdout.write(
                    f'  {num_tasks:2d} tasks × {CONNECTIONS_PER_TASK} conns = {total_conns} (OK)'
                )

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Autoscaling from 10 to 50 tasks on traffic spike'
            '\n  - t=0: 10 tasks × 10 conns = 100 (at limit)'
            '\n  - t=30s: Autoscaler adds 10 tasks -> 200 connections -> ERRORS'
            '\n  - New tasks cannot connect -> health check fails -> removed'
            '\n  - Existing tasks see intermittent connection refused errors'
            '\n  - DB CPU 80%+ just tracking/killing idle connections'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - RDS max_connections = RAM-based formula (often < 200)')
        self.stdout.write('  - Each Django process holds CONN_MAX_AGE connections open')
        self.stdout.write('  - Solution: RDS Proxy (connection pooling at AWS level)')
        self.stdout.write('  - Or: PgBouncer for PostgreSQL connection pooling')
