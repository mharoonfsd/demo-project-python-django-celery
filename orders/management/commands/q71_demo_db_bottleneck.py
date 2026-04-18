from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q71 PROBLEM: Scaling ECS containers to handle load, but the database
    is the real bottleneck. More containers = more DB connections =
    DB overwhelmed. Adding compute doesn't help when DB is saturated.
    """
    help = 'Q71 Problem: Scaling ECS but DB is the bottleneck'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q71 PROBLEM: DB bottleneck hidden by ECS scaling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q71-ORD-{i:03}',
                customer_email=f'q71user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        DB_MAX_CONNECTIONS = 100
        CONNECTIONS_PER_TASK = 10
        MAX_DB_THROUGHPUT = 1000  # queries/sec at saturation

        def simulate_scale_out(num_tasks, incoming_rps):
            connections_used = num_tasks * CONNECTIONS_PER_TASK
            capacity_exhausted = connections_used >= DB_MAX_CONNECTIONS
            db_rps = min(MAX_DB_THROUGHPUT, incoming_rps)
            p99_latency_ms = 50 if not capacity_exhausted else 2000 + (connections_used - DB_MAX_CONNECTIONS) * 100
            return {
                'tasks': num_tasks,
                'connections': connections_used,
                'conn_exhausted': capacity_exhausted,
                'p99_ms': p99_latency_ms,
            }

        self.stdout.write('Scaling ECS tasks under load (1000 req/s incoming):')
        for tasks in [2, 5, 10, 15]:
            result = simulate_scale_out(tasks, 1000)
            if result['conn_exhausted']:
                self.stdout.write(self.style.ERROR(
                    f'  {tasks} tasks: {result["connections"]} connections '
                    f'(OVER LIMIT), p99={result["p99_ms"]}ms <- DB saturated!'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  {tasks} tasks: {result["connections"]} connections, '
                    f'p99={result["p99_ms"]}ms'
                ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: More ECS tasks = more DB connections = worse performance'
            '\n  - DB has fixed connection limit (RDS: 100-1000 depending on size)'
            '\n  - Each task opens connection pool on startup'
            '\n  - Adding tasks past DB limit = cascade failures'
            '\n  - Scaling compute doesn\'t solve DB I/O bottleneck'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Profile WHERE the bottleneck is before scaling')
        self.stdout.write('  - Use RDS Proxy to pool DB connections')
        self.stdout.write('  - Add read replicas for read-heavy workloads')
        self.stdout.write('  - Cache frequently-read data (Redis/ElastiCache)')
