from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q78 PROBLEM: ECS service has no rate limiting. A single client or runaway
    process sends unlimited requests. Without rate limiting, one bad actor
    can consume all capacity, causing timeouts for legitimate users.
    """
    help = 'Q78 Problem: No rate limiting - one client exhausts all capacity'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q78 PROBLEM: No rate limiting - capacity exhausted')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q78-ORDER',
            customer_email='q78@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        SERVICE_CAPACITY = 100  # requests/second

        clients = [
            {'id': 'client-A', 'rps': 80},   # bad actor / bug
            {'id': 'client-B', 'rps': 20},   # normal client
            {'id': 'client-C', 'rps': 20},   # normal client
        ]

        total_rps = sum(c['rps'] for c in clients)

        self.stdout.write(f'Service capacity: {SERVICE_CAPACITY} req/s')
        self.stdout.write(f'Total incoming: {total_rps} req/s')
        self.stdout.write('')
        self.stdout.write('Request allocation (no rate limiting):')

        for client in clients:
            share = client['rps'] / total_rps
            served = int(share * SERVICE_CAPACITY)
            if client['id'] == 'client-A':
                self.stdout.write(self.style.ERROR(
                    f'  {client["id"]}: {client["rps"]} rps -> served {served} (monopolizes {share*100:.0f}%)'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  {client["id"]}: {client["rps"]} rps -> only gets ~{served} (starved)'
                ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: client-A bug/attack takes 67% of capacity'
            '\n  - client-B and client-C get fewer requests served'
            '\n  - Service latency spikes for all users'
            '\n  - No way to identify or stop the offending client'
            '\n  - No per-client metrics to diagnose the issue'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always implement rate limiting per client/IP/API key')
        self.stdout.write('  - Use ALB with WAF rate-based rules')
        self.stdout.write('  - Implement token bucket in application (Django Ratelimit)')
        self.stdout.write('  - Return 429 Too Many Requests with Retry-After header')
