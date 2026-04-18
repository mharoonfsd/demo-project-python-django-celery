from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q76 SOLUTION: Use RDS Proxy to decouple DB connections from task count.
    Scale in smaller steps. Cap max tasks. Implement connection pre-warming.
    """
    help = 'Q76 Solution: Prevent autoscaling amplification with RDS Proxy'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q76 SOLUTION: Safe autoscaling with RDS Proxy')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q76-SOL-ORDER',
            customer_email='q76sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # With RDS Proxy: many tasks share a small pool to the DB
        PROXY_DB_CONNECTIONS = 10   # RDS Proxy maintains 10 connections to RDS
        CONNECTIONS_PER_TASK = 10   # Tasks connect to proxy (not DB directly)
        DB_MAX_CONNECTIONS = 100

        self.stdout.write('With RDS Proxy:')
        for tasks in [2, 5, 10, 20, 50]:
            task_to_proxy_conns = tasks * CONNECTIONS_PER_TASK
            proxy_to_db_conns = PROXY_DB_CONNECTIONS  # fixed!
            self.stdout.write(self.style.SUCCESS(
                f'  {tasks} tasks -> {task_to_proxy_conns} proxy conns -> '
                f'{proxy_to_db_conns} actual DB conns (fixed)'
            ))

        self.stdout.write('')
        self.stdout.write('Safe scaling configuration:')
        self.stdout.write(f'  Scale step: +2 tasks (not +10)')
        self.stdout.write(f'  Scale-out cooldown: 30s')
        self.stdout.write(f'  Scale-in cooldown: 300s')
        max_safe_tasks = DB_MAX_CONNECTIONS // CONNECTIONS_PER_TASK
        self.stdout.write(self.style.SUCCESS(
            f'  Max tasks without RDS Proxy: {max_safe_tasks}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'  Max tasks with RDS Proxy: unlimited (proxy handles connections)'
        ))

        self.stdout.write('\nRDS Proxy configuration:')
        self.stdout.write('  - ConnectionPoolMaxConnections: 10 (to RDS)')
        self.stdout.write('  - BorrowTimeout: 30s')
        self.stdout.write('  - MaxConnectionsPercent: 100')
        self.stdout.write('  - Tasks connect to proxy endpoint (not RDS endpoint)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - RDS Proxy decouples connection count from task count')
        self.stdout.write('  - Scale in smaller steps to reduce connection storm risk')
        self.stdout.write('  - Set max tasks = DB_MAX_CONNS / CONNS_PER_TASK (without proxy)')
        self.stdout.write('  - RDS Proxy cost: ~$0.015/vCPU/hour (worth it at scale)')
