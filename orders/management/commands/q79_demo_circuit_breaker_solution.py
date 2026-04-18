from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q79 SOLUTION: Implement circuit breaker pattern. Track failure rate.
    When failure threshold exceeded, OPEN circuit and fail immediately.
    After cooldown, move to HALF-OPEN and test recovery.
    """
    help = 'Q79 Solution: Circuit breaker pattern implementation'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q79 SOLUTION: Circuit breaker prevents cascading failure')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q79-SOL-{i:03}',
                customer_email=f'q79sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        class CircuitBreaker:
            CLOSED = 'CLOSED'
            OPEN = 'OPEN'
            HALF_OPEN = 'HALF_OPEN'

            def __init__(self, failure_threshold=3, recovery_calls=2):
                self.state = self.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.failure_threshold = failure_threshold
                self.recovery_calls = recovery_calls

            def call(self, fn, *args, **kwargs):
                if self.state == self.OPEN:
                    raise Exception('CircuitBreaker OPEN: failing fast')

                try:
                    result = fn(*args, **kwargs)
                    if self.state == self.HALF_OPEN:
                        self.success_count += 1
                        if self.success_count >= self.recovery_calls:
                            self.state = self.CLOSED
                            self.failure_count = 0
                            self.success_count = 0
                    return result
                except Exception:
                    self.failure_count += 1
                    if self.failure_count >= self.failure_threshold:
                        self.state = self.OPEN
                    raise

        cb = CircuitBreaker(failure_threshold=3)

        def payment_service(order_id, service_healthy):
            if not service_healthy:
                raise ConnectionError(f'Payment service timeout')
            return f'charged order {order_id}'

        scenarios = [
            (1, False, 'service DOWN'),
            (2, False, 'service DOWN'),
            (3, False, 'service DOWN -> opens circuit'),
            (4, False, 'circuit OPEN -> fast fail'),
            (5, False, 'circuit OPEN -> fast fail'),
        ]

        self.stdout.write('Requests with circuit breaker:')
        import sys
        for order_id, healthy, note in scenarios:
            try:
                start_state = cb.state
                result = cb.call(payment_service, order_id, healthy)
                self.stdout.write(self.style.SUCCESS(f'  order {order_id}: OK - {result}'))
            except Exception as e:
                if cb.state == cb.OPEN and 'failing fast' in str(e):
                    self.stdout.write(self.style.WARNING(
                        f'  order {order_id}: FAST FAIL <1ms [{cb.state}] - {note}'
                    ))
                else:
                    self.stdout.write(
                        f'  order {order_id}: timeout (30s) [{cb.state}] - {note}'
                    )

        self.stdout.write('\nCircuit breaker recovery (service comes back):')
        cb.state = cb.HALF_OPEN
        cb.success_count = 0
        for i, healthy in [(1, True), (2, True)]:
            try:
                result = cb.call(payment_service, i, healthy)
                self.stdout.write(self.style.SUCCESS(
                    f'  Test call {i}: OK [{cb.state}]'
                ))
            except Exception as e:
                self.stdout.write(f'  Test call {i}: failed')
        self.stdout.write(self.style.SUCCESS(f'  Circuit CLOSED - normal operation resumed'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - CLOSED: normal, track failures')
        self.stdout.write('  - OPEN: fail fast immediately, skip timeout wait')
        self.stdout.write('  - HALF_OPEN: allow few test requests to check recovery')
        self.stdout.write('  - Use libraries: circuitbreaker, pybreaker, or tenacity')
