from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q79 PROBLEM: No circuit breaker pattern. When a downstream service
    is slow or failing, all requests wait for the full timeout. Worker
    threads pile up waiting, exhausting thread pool and taking down the caller.
    """
    help = 'Q79 Problem: No circuit breaker - cascading failure from slow dependency'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q79 PROBLEM: No circuit breaker - cascading failure')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 5):
            Order.objects.create(
                order_number=f'Q79-ORD-{i:03}',
                customer_email=f'q79user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        TIMEOUT_SECONDS = 30  # request timeout to payment service
        THREAD_POOL_SIZE = 10
        threads_in_use = 0
        requests_processed = 0

        def call_payment_service_no_cb(order_id, payment_service_down):
            nonlocal threads_in_use, requests_processed
            threads_in_use += 1
            if payment_service_down:
                # Waits full 30s before failing - blocks the thread
                self.stdout.write(
                    f'  order {order_id}: waiting {TIMEOUT_SECONDS}s for payment service... TIMEOUT'
                )
                threads_in_use -= 1
                return False
            requests_processed += 1
            threads_in_use -= 1
            return True

        self.stdout.write(f'Thread pool size: {THREAD_POOL_SIZE}')
        self.stdout.write(f'Request timeout: {TIMEOUT_SECONDS}s')
        self.stdout.write(f'Payment service: DOWN\n')

        orders = list(Order.objects.all()[:4])
        self.stdout.write('Requests without circuit breaker:')
        for order in orders:
            call_payment_service_no_cb(order.pk, payment_service_down=True)

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: Each request waits {TIMEOUT_SECONDS}s before failing'
            f'\n  - {len(orders)} requests × {TIMEOUT_SECONDS}s = {len(orders) * TIMEOUT_SECONDS}s of wasted waiting'
            f'\n  - Thread pool exhausted: {THREAD_POOL_SIZE} threads waiting on timeouts'
            f'\n  - New requests queued or rejected'
            f'\n  - Service caller is now also degraded (cascading failure)'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Without circuit breaker, failures cascade instantly')
        self.stdout.write('  - Thread pool exhaustion causes caller to fail too')
        self.stdout.write('  - Circuit breaker: fail fast when dependency is down')
        self.stdout.write('  - States: CLOSED (normal) -> OPEN (failing fast) -> HALF-OPEN (testing)')
