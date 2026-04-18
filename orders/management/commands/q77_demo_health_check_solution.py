from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q77 SOLUTION: Configure ECS health check + ALB target group health check.
    Implement /health endpoint that checks DB and dependencies.
    Set healthCheckGracePeriodSeconds to cover app warmup.
    """
    help = 'Q77 Solution: Proper health check configuration'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q77 SOLUTION: Health check prevents premature traffic')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q77-SOL-ORDER',
            customer_email='q77sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        APP_WARMUP_SECONDS = 30

        self.stdout.write('Health check implementation (/health endpoint):')
        def health_check_handler(db_ready, redis_ready, app_ready):
            """Simulates /health endpoint logic."""
            if not db_ready:
                return 503, {'status': 'unhealthy', 'reason': 'DB not connected'}
            if not redis_ready:
                return 503, {'status': 'unhealthy', 'reason': 'Redis not connected'}
            if not app_ready:
                return 503, {'status': 'unhealthy', 'reason': 'App still warming up'}
            return 200, {'status': 'healthy'}

        checks = [
            (False, False, False, 't=5s: warmup phase'),
            (True, False, False, 't=15s: DB connected, Redis pending'),
            (True, True, False, 't=25s: Redis connected, app warming up'),
            (True, True, True, 't=30s: fully ready'),
        ]

        self.stdout.write('')
        for db, redis, app, label in checks:
            code, body = health_check_handler(db, redis, app)
            if code == 200:
                self.stdout.write(self.style.SUCCESS(f'  {label}: {code} {body}'))
            else:
                self.stdout.write(f'  {label}: {code} {body}')

        self.stdout.write('\nECS task definition health check:')
        self.stdout.write('  "healthCheck": {')
        self.stdout.write('      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],')
        self.stdout.write('      "interval": 10,')
        self.stdout.write('      "timeout": 5,')
        self.stdout.write('      "retries": 3,')
        self.stdout.write(f'      "startPeriod": {APP_WARMUP_SECONDS + 10}')
        self.stdout.write('  }')

        self.stdout.write('\nALB target group config:')
        self.stdout.write('  HealthCheckPath: /health')
        self.stdout.write('  HealthyThresholdCount: 2')
        self.stdout.write('  UnhealthyThresholdCount: 3')
        self.stdout.write(f'  HealthCheckIntervalSeconds: 10')
        self.stdout.write(f'  Service healthCheckGracePeriodSeconds: {APP_WARMUP_SECONDS + 15}')

        self.stdout.write('\nStartup timeline (with health check):')
        self.stdout.write('  t=0s: Container started')
        self.stdout.write('  t=0-30s: Health checks return 503 -> no traffic sent')
        self.stdout.write('  t=30s: Health checks pass')
        self.stdout.write(self.style.SUCCESS('  t=30s: Load balancer starts sending traffic -> 0 errors'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Implement /health endpoint checking all dependencies')
        self.stdout.write('  - Set startPeriod > app warmup to avoid false failures')
        self.stdout.write('  - ALB + ECS health checks both needed (different purposes)')
        self.stdout.write('  - Health check should be fast (<500ms) and lightweight')
