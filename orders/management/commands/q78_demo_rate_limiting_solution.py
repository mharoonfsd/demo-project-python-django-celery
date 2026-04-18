from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q78 SOLUTION: Implement token bucket rate limiting per client.
    Return 429 when limit exceeded. Use Redis for distributed rate limiting
    across multiple ECS tasks.
    """
    help = 'Q78 Solution: Token bucket rate limiting per client'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q78 SOLUTION: Rate limiting with token bucket')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q78-SOL-ORDER',
            customer_email='q78sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        RATE_LIMIT_PER_CLIENT = 30  # max 30 req/s per client

        class TokenBucket:
            def __init__(self, capacity, refill_rate):
                self.capacity = capacity
                self.tokens = capacity
                self.refill_rate = refill_rate

            def allow(self):
                if self.tokens > 0:
                    self.tokens -= 1
                    return True
                return False  # 429

            def refill(self, count):
                self.tokens = min(self.capacity, self.tokens + count)

        buckets = {
            'client-A': TokenBucket(RATE_LIMIT_PER_CLIENT, RATE_LIMIT_PER_CLIENT),
            'client-B': TokenBucket(RATE_LIMIT_PER_CLIENT, RATE_LIMIT_PER_CLIENT),
            'client-C': TokenBucket(RATE_LIMIT_PER_CLIENT, RATE_LIMIT_PER_CLIENT),
        }

        requests = [
            ('client-A', 40),  # bad actor: 40 requests
            ('client-B', 20),  # normal
            ('client-C', 20),  # normal
        ]

        self.stdout.write(f'Rate limit: {RATE_LIMIT_PER_CLIENT} req/s per client')
        self.stdout.write('')
        self.stdout.write('Request handling with rate limiting:')
        for client_id, count in requests:
            bucket = buckets[client_id]
            allowed = 0
            throttled = 0
            for _ in range(count):
                if bucket.allow():
                    allowed += 1
                else:
                    throttled += 1
            if throttled > 0:
                self.stdout.write(self.style.WARNING(
                    f'  {client_id}: {allowed} allowed, {throttled} throttled (429)'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  {client_id}: {allowed} allowed, {throttled} throttled'
                ))

        self.stdout.write('\nRedis-based distributed rate limiting:')
        self.stdout.write('  import redis')
        self.stdout.write('  def is_allowed(client_id, limit=30, window=1):')
        self.stdout.write('      key = f"rate:{client_id}:{int(time.time() // window)}"')
        self.stdout.write('      count = r.incr(key)')
        self.stdout.write('      r.expire(key, window * 2)')
        self.stdout.write('      return count <= limit')
        self.stdout.write('')
        self.stdout.write('  # In Django view:')
        self.stdout.write('  if not is_allowed(request.META["HTTP_X_API_KEY"]):')
        self.stdout.write('      return HttpResponse(status=429, headers={"Retry-After": "1"})')

        self.stdout.write('\nAWS WAF rate-based rule:')
        self.stdout.write('  Limit: 2000 requests per 5-minute window per IP')
        self.stdout.write('  Action: Block (returns 403)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Token bucket or sliding window counter per client')
        self.stdout.write('  - Redis INCR + EXPIRE for distributed rate limiting')
        self.stdout.write('  - Return 429 with Retry-After header')
        self.stdout.write('  - AWF WAF: coarse IP-level protection at edge')
