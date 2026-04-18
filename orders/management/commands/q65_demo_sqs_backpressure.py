from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q65 PROBLEM: SQS consumer processes messages in tight loop with no
    backpressure. When a downstream service is slow, messages pile up faster
    than they're processed. Consumer overwhelms DB, Redis, or external APIs.
    """
    help = 'Q65 Problem: No backpressure - consumer overwhelms downstream'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q65 PROBLEM: SQS consumer with no backpressure')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 11):
            Order.objects.create(
                order_number=f'Q65-ORD-{i:03}',
                customer_email=f'q65user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Simulate: DB can handle 5 req/s, consumer sends 50 req/s
        db_capacity = 5      # requests per second
        consumer_rate = 50   # requests per second (no throttle)
        queue_depth = 100

        self.stdout.write(f'DB capacity: {db_capacity} req/s')
        self.stdout.write(f'Consumer rate: {consumer_rate} req/s (unthrottled)')
        self.stdout.write(f'Initial queue depth: {queue_depth} messages')

        self.stdout.write('\nSimulating consumer behavior (no backpressure):')
        errors = 0
        processed = 0
        for t in range(1, 6):
            sent = min(consumer_rate, queue_depth)
            overflow = max(0, sent - db_capacity)
            accepted = sent - overflow
            processed += accepted
            errors += overflow
            queue_depth -= accepted
            self.stdout.write(
                f'  t={t}s: sent={sent}, DB accepted={accepted}, '
                f'DB errors={overflow}, queue_depth={queue_depth}'
            )

        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: {errors} DB errors, {processed} processed'
            '\n  - DB overwhelmed with connection/timeout errors'
            '\n  - Consumer retries failed messages = MORE load on DB'
            '\n  - Cascading failure: DB -> consumer -> more retries -> more DB load'
            '\n  - No rate limiting or concurrency control'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always limit concurrency in SQS consumers')
        self.stdout.write('  - Use semaphores or thread pool with max workers')
        self.stdout.write('  - Implement exponential backoff on downstream errors')
        self.stdout.write('  - Monitor consumer lag and DB connection pool usage')
