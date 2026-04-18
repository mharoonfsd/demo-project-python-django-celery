from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q72 PROBLEM: ECS tasks receive more work than they can process (backpressure).
    Input rate exceeds output rate. No mechanism to slow down producers.
    Queue grows unboundedly until system collapses.
    """
    help = 'Q72 Problem: ECS backpressure - input rate exceeds processing rate'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q72 PROBLEM: ECS backpressure - queue growing unboundedly')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q72-ORDER',
            customer_email='q72@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        input_rate = 100   # messages/second
        process_rate = 40  # messages/second (ECS capacity)
        queue_depth = 0
        max_queue = 10000

        self.stdout.write(f'Input rate: {input_rate} msg/s')
        self.stdout.write(f'ECS process rate: {process_rate} msg/s')
        self.stdout.write(f'Overflow: {input_rate - process_rate} msg/s')
        self.stdout.write('')
        self.stdout.write('Queue depth over time (no backpressure):')

        for t in range(1, 8):
            queue_depth += (input_rate - process_rate)
            queue_depth = min(queue_depth, max_queue)
            status = '<- QUEUE FULL!' if queue_depth >= max_queue else ''
            self.stdout.write(
                f'  t={t}s: depth={queue_depth} {status}'
            )
            if queue_depth >= max_queue:
                self.stdout.write(self.style.ERROR(
                    '  Messages being DROPPED (queue full)'
                ))
                break

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No backpressure mechanism\n'
            '  - Queue fills up in seconds\n'
            '  - Adding more ECS tasks takes 2-3 minutes (cold start)\n'
            '  - Messages dropped or expire during that window\n'
            '  - System never stabilizes if input > max ECS capacity'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Monitor queue depth and autoscale ECS proactively')
        self.stdout.write('  - Use SQS queue depth as scaling metric (not just CPU)')
        self.stdout.write('  - Implement producer rate limiting when queue is deep')
        self.stdout.write('  - Set max tasks high enough to drain at peak load')
