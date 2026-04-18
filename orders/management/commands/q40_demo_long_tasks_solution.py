from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import asyncio
import time


class Command(BaseCommand):
    """
    Q40 SOLUTION: Separate workers by task type or priority. Use dedicated
    workers for long tasks and short tasks. Alternatively, use async/await
    or gevent to make I/O non-blocking. Break long tasks into smaller chunks.
    """
    help = 'Q40 Solution: Task isolation and async patterns'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q40 SOLUTION: Task isolation and async patterns')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Solution 1: Separate queues for long vs short tasks
        @app.task(queue='long_tasks')
        def slow_task(order_id):
            """Queued to dedicated 'long_tasks' queue."""
            self.stdout.write(f'  Slow task (dedicated worker pool)')
            time.sleep(3)
            return 'done'

        @app.task(queue='short_tasks')
        def fast_task(order_id):
            """Queued to dedicated 'short_tasks' queue."""
            self.stdout.write(f'  Fast task (responsive pool)')
            return 'quick'

        order = Order.objects.create(
            order_number='Q40-SOL-ORDER',
            customer_email='q40sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nSolution 1: Dedicated worker pools')
        self.stdout.write('  celery -A demo_project worker -Q short_tasks (concurrency=20)')
        self.stdout.write('  celery -A demo_project worker -Q long_tasks (concurrency=4)')
        self.stdout.write('')
        self.stdout.write('  Fast tasks: responsive, no contention')
        self.stdout.write('  Slow tasks: isolated, don\'t starve others')

        # Solution 2: Chunk long tasks
        @app.task
        def chunked_task(order_id, chunk_num):
            """Break into small, fast chunks."""
            self.stdout.write(f'  Processing chunk {chunk_num}')
            time.sleep(0.5)  # Small work unit
            if chunk_num < 3:
                # Queue next chunk
                chunked_task.delay(order_id, chunk_num + 1)
            return 'done'

        self.stdout.write('\nSolution 2: Chunk long tasks')
        self.stdout.write('  chunked_task(order_id, chunk=1)')
        self.stdout.write('  -> Each chunk: 0.5s, unblocks worker')
        self.stdout.write('  -> Between chunks, other tasks run')

        # Solution 3: Use time_limit
        @app.task(time_limit=30, soft_time_limit=25)
        def bounded_task(order_id):
            """Enforce maximum execution time."""
            self.stdout.write(f'  Task with 25s soft limit')
            return 'done'

        self.stdout.write('\nSolution 3: Time limits')
        self.stdout.write('  @app.task(soft_time_limit=30, time_limit=35)')
        self.stdout.write('  -> Forces task to complete or raise exception')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Separate workers for long vs short tasks')
        self.stdout.write('  - Use task_queue or routing to direct tasks')
        self.stdout.write('  - Break long tasks into small chunks')
        self.stdout.write('  - Use soft/hard time limits to prevent starvation')
