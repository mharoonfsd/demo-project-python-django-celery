from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q55 PROBLEM: SNS retries failed deliveries with exponential backoff, but
    without proper retry policies and subscriber health checks, you get a
    'retry storm' — the failing endpoint is overwhelmed by retry attempts
    from multiple SNS topics simultaneously.
    """
    help = 'Q55 Problem: SNS retry storm overwhelming the endpoint'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q55 PROBLEM: SNS retry storm')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q55-ORDER',
            customer_email='q55@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate SNS retry behaviour without backoff strategy
        self.stdout.write('Simulating SNS delivery attempts (no backoff config):')
        self.stdout.write('')

        def attempt_delivery(attempt, endpoint_healthy):
            if endpoint_healthy:
                self.stdout.write(f'  Attempt {attempt}: OK')
                return True
            self.stdout.write(self.style.ERROR(f'  Attempt {attempt}: FAILED (503)'))
            return False

        # SNS default: 3 immediate, then 20 retries over 1 hour
        immediate_retries = 3
        endpoint_healthy = False

        total_attempts = 0
        topics = ['orders', 'payments', 'inventory']

        for topic in topics:
            self.stdout.write(f'\nTopic: {topic}')
            for i in range(1, immediate_retries + 1):
                total_attempts += 1
                attempt_delivery(i, endpoint_healthy)

        self.stdout.write(self.style.ERROR(
            f'\nTotal failed attempts in burst: {total_attempts}'
        ))
        self.stdout.write(self.style.ERROR(
            'PROBLEM: Endpoint receives retry storm\n'
            '  - 3 topics × 3 immediate retries = 9 requests instantly\n'
            '  - Then 20 more retries per topic = 60+ more requests\n'
            '  - Overwhelmed endpoint stays down longer\n'
            '  - Messages back-pressure into queue\n'
            '  - System never recovers'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SNS default: numRetries=3 immediate + up to 100,000 total')
        self.stdout.write('  - Configure delivery retry policy per subscription')
        self.stdout.write('  - Use SQS as SNS subscriber (buffers the storm)')
        self.stdout.write('  - Add circuit breaker at the HTTP endpoint level')
