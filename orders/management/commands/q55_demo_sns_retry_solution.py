from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q55 SOLUTION: Configure SNS delivery retry policy with exponential backoff.
    Use SQS as a buffer between SNS and HTTP endpoints. Add circuit breaker.
    """
    help = 'Q55 Solution: SNS retry policy and circuit breaker'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q55 SOLUTION: SNS retry policy with backoff')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q55-SOL-ORDER',
            customer_email='q55sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('SNS delivery retry policy configuration:')
        retry_policy = {
            'numRetries': 3,
            'numMaxDelayRetries': 10,
            'minDelayTarget': 20,      # seconds
            'maxDelayTarget': 300,     # 5 minutes
            'numNoDelayRetries': 0,
            'backoffFunction': 'exponential',
        }
        for k, v in retry_policy.items():
            self.stdout.write(f'  {k}: {v}')

        self.stdout.write('\nSimulated delivery with exponential backoff:')
        endpoint_healthy = False
        delay = retry_policy['minDelayTarget']
        circuit_open = False
        failure_count = 0
        circuit_threshold = 3

        for attempt in range(1, 6):
            if circuit_open:
                self.stdout.write(self.style.WARNING(
                    f'  Attempt {attempt}: Circuit OPEN — skipping, waiting for recovery'
                ))
                continue

            if endpoint_healthy:
                self.stdout.write(self.style.SUCCESS(f'  Attempt {attempt}: OK'))
                failure_count = 0
                circuit_open = False
            else:
                self.stdout.write(f'  Attempt {attempt}: FAILED (next retry in {delay}s)')
                failure_count += 1
                delay = min(delay * 2, retry_policy['maxDelayTarget'])

                if failure_count >= circuit_threshold:
                    circuit_open = True
                    self.stdout.write(self.style.WARNING(
                        f'  Circuit breaker OPENED after {failure_count} failures'
                    ))

        self.stdout.write('\nArchitecture recommendation: SNS -> SQS -> Lambda/ECS')
        self.stdout.write('  - SNS publishes to SQS (never directly to HTTP in prod)')
        self.stdout.write('  - SQS buffers messages during outages')
        self.stdout.write('  - Consumer pulls at its own pace')
        self.stdout.write('  - No retry storm possible')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Configure exponential backoff in SNS delivery policy')
        self.stdout.write('  - Prefer SQS subscriber over HTTP for resilience')
        self.stdout.write('  - Use circuit breaker to halt retries during outage')
        self.stdout.write('  - Set DLQ on SQS to capture unprocessable messages')
