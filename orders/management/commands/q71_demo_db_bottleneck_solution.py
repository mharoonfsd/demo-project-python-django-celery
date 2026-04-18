from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q71 SOLUTION: Use RDS Proxy to pool DB connections, add read replicas
    for read-heavy queries, and cache hot data in Redis. Profile first to
    identify actual bottleneck before throwing more containers at the problem.
    """
    help = 'Q71 Solution: Fix DB bottleneck with proxy, replicas, caching'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q71 SOLUTION: Fix DB bottleneck correctly')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q71-SOL-{i:03}',
                customer_email=f'q71sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        self.stdout.write('Step 1: Profile to find bottleneck')
        self.stdout.write('  pg_stat_statements: identify slow queries')
        self.stdout.write('  EXPLAIN ANALYZE: check missing indexes')
        self.stdout.write('  CloudWatch: DBConnections, CPUUtilization, ReadIOPS')
        self.stdout.write('')

        self.stdout.write('Step 2: RDS Proxy (connection pooling)')
        self.stdout.write('  - Proxy maintains pool of persistent DB connections')
        self.stdout.write('  - ECS tasks connect to proxy, not DB directly')
        self.stdout.write('  - 100 tasks × 10 conns = 1000 proxy conns -> 5-10 actual DB conns')

        PROXY_CONNECTIONS_TO_DB = 10
        ECS_TASKS = 100
        TASK_CONNECTIONS = 10
        self.stdout.write(self.style.SUCCESS(
            f'  Without proxy: {ECS_TASKS * TASK_CONNECTIONS} DB connections'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'  With RDS Proxy: only {PROXY_CONNECTIONS_TO_DB} actual DB connections'
        ))

        self.stdout.write('')
        self.stdout.write('Step 3: Read replicas for read-heavy workloads')
        self.stdout.write('  # Django multi-DB routing')
        self.stdout.write('  DATABASES = {')
        self.stdout.write('      "default": {"HOST": "rds-primary.cluster..."},')
        self.stdout.write('      "read_replica": {"HOST": "rds-reader.cluster..."},')
        self.stdout.write('  }')
        self.stdout.write('  Order.objects.using("read_replica").filter(...)')
        self.stdout.write('')

        self.stdout.write('Step 4: Cache hot data')
        self.stdout.write('  from django.core.cache import cache')
        self.stdout.write('  def get_order(pk):')
        self.stdout.write('      key = f"order:{pk}"')
        self.stdout.write('      result = cache.get(key)')
        self.stdout.write('      if result is None:')
        self.stdout.write('          result = Order.objects.get(pk=pk)')
        self.stdout.write('          cache.set(key, result, timeout=300)')
        self.stdout.write('      return result')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Profile FIRST: is it CPU, DB I/O, or connection count?')
        self.stdout.write('  - RDS Proxy: multiplexes connections, great for Lambda/ECS')
        self.stdout.write('  - Read replicas: offload 80%+ of typical web traffic')
        self.stdout.write('  - Redis caching: reduce DB load by 90% for hot data')
