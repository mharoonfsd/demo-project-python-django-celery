from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q77 PROBLEM: ECS service has no health check configured. Containers
    start and register with the load balancer immediately, even though the
    app needs 30+ seconds to warm up. Requests fail during warmup period.
    """
    help = 'Q77 Problem: Missing health check - traffic sent before app ready'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q77 PROBLEM: No health check - traffic before ready')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q77-ORDER',
            customer_email='q77@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        APP_WARMUP_SECONDS = 30
        NO_HEALTH_CHECK = True

        self.stdout.write(f'ECS service config:')
        self.stdout.write(f'  healthCheck: None (not configured)')
        self.stdout.write(f'  App warmup time: {APP_WARMUP_SECONDS}s')
        self.stdout.write('')

        startup_events = [
            (0, 'Container started'),
            (0, 'Registered with load balancer (no health check = immediate!)'),
            (2, 'User request arrives -> 502 Bad Gateway (app not ready)'),
            (5, 'User request -> 502'),
            (10, 'User request -> 502'),
            (30, 'App fully initialized'),
            (31, 'Requests now succeed'),
        ]

        self.stdout.write('Startup timeline (no health check):')
        for t, event in startup_events:
            if '502' in event:
                self.stdout.write(self.style.ERROR(f'  t={t}s: {event}'))
            elif 'immediately' in event:
                self.stdout.write(self.style.WARNING(f'  t={t}s: {event}'))
            else:
                self.stdout.write(f'  t={t}s: {event}')

        error_window = 30 - 2
        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: {error_window}s window of user-facing errors per deployment'
            '\n  - Rolling deploys: some requests go to old task, some to new (not ready)'
            '\n  - Blue/green: entire cutover before health confirmed'
            '\n  - Load balancer unhealthy task detection: too slow without health check'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Define healthCheck in ECS task definition')
        self.stdout.write('  - Add /health endpoint to your application')
        self.stdout.write('  - Set healthCheckGracePeriodSeconds > app warmup time')
        self.stdout.write('  - Load balancer only sends traffic after health checks pass')
