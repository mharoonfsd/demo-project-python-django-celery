from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q83 SOLUTION: Use RDS Proxy to multiplex many ECS connections into
    a smaller pool of actual DB connections. Set CONN_MAX_AGE=0 for
    serverless/Fargate. Use PgBouncer as self-managed alternative.
    """
    help = 'Q83 Solution: RDS Proxy for connection pooling'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q83 SOLUTION: RDS Proxy multiplexes ECS connections')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q83-SOL-ORDER',
            customer_email='q83sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        RDS_MAX_CONNECTIONS = 100
        PROXY_POOL_SIZE = 20      # RDS Proxy -> RDS: only 20 real DB connections
        CONNECTIONS_PER_TASK = 10

        self.stdout.write('Architecture: ECS tasks -> RDS Proxy -> RDS')
        self.stdout.write(f'RDS Proxy pool size (to RDS): {PROXY_POOL_SIZE}')
        self.stdout.write(f'RDS max_connections: {RDS_MAX_CONNECTIONS}')
        self.stdout.write('')

        self.stdout.write('Connection handling with RDS Proxy:')
        for num_tasks in [5, 10, 15, 20, 50]:
            task_to_proxy = num_tasks * CONNECTIONS_PER_TASK
            proxy_to_rds = min(PROXY_POOL_SIZE, task_to_proxy)
            self.stdout.write(self.style.SUCCESS(
                f'  {num_tasks:2d} tasks -> proxy: {task_to_proxy:4d} conns -> '
                f'RDS: {proxy_to_rds:3d} conns OK'
            ))

        self.stdout.write('\nDjango settings for RDS Proxy:')
        self.stdout.write('  DATABASES = {')
        self.stdout.write('      "default": {')
        self.stdout.write('          "HOST": "myapp.proxy-xxx.rds.amazonaws.com",  # Proxy endpoint')
        self.stdout.write('          "CONN_MAX_AGE": 0,  # Disable persistent connections on Fargate')
        self.stdout.write('      }')
        self.stdout.write('  }')

        self.stdout.write('\nAlternative: PgBouncer (self-managed, PostgreSQL only):')
        self.stdout.write('  pool_mode = transaction')
        self.stdout.write('  max_client_conn = 1000')
        self.stdout.write('  default_pool_size = 20')
        self.stdout.write('  # 50 tasks × 10 conns -> PgBouncer -> 20 real DB conns')

        self.stdout.write('\nCONN_MAX_AGE guidance:')
        self.stdout.write('  - Long-running servers (Gunicorn): CONN_MAX_AGE=60')
        self.stdout.write('  - Fargate/Lambda/Celery workers: CONN_MAX_AGE=0')
        self.stdout.write('  - With RDS Proxy: CONN_MAX_AGE=0 (proxy handles pooling)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - RDS Proxy decouples application connections from DB connections')
        self.stdout.write('  - Scale ECS tasks freely without worrying about max_connections')
        self.stdout.write('  - Proxy also provides failover, IAM auth, and secret rotation')
        self.stdout.write('  - CONN_MAX_AGE=0 on Fargate to avoid ghost connections')
