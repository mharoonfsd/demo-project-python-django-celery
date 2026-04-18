from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import time


class Command(BaseCommand):
    """
    Q40 PROBLEM: Celery workers use an event loop (gevent, eventlet, or threads).
    Long-running synchronous code blocks the event loop, preventing other tasks
    from running. A single slow task starves all other tasks on that worker.
    """
    help = 'Q40 Problem: Long blocking tasks starve the worker'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q40 PROBLEM: Blocking tasks starve worker event loop')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @app.task
        def slow_blocking_task(order_id):
            """Long-running synchronous operation."""
            self.stdout.write(f'  Starting slow task...')
            # Simulate: blocking operation (e.g., old API call, file I/O)
            start = time.time()
            for i in range(30):
                time.sleep(0.1)  # 3 seconds total
            duration = time.time() - start
            self.stdout.write(f'  Slow task done ({duration:.1f}s)')
            return 'done'

        @app.task
        def fast_task(order_id):
            """Quick task."""
            self.stdout.write(f'  Fast task running')
            return 'quick'

        self.stdout.write('\nScenario: Single worker (concurrency=4)')
        self.stdout.write('  All 4 concurrent slots occupied by slow tasks')
        self.stdout.write('')

        self.stdout.write('Enqueue 4 slow tasks:')
        for i in range(4):
            self.stdout.write(f'  slow_blocking_task queued')
            slow_blocking_task.delay(i)

        self.stdout.write('\nTry to enqueue fast task:')
        self.stdout.write('  fast_task queued')
        self.stdout.write('  -> But all 4 workers are blocked on slow tasks!')
        self.stdout.write('  -> Fast task sits in queue, waiting 3+ seconds')

        self.stdout.write(self.style.WARNING(
            '\nPROBLEM: Event loop starvation\n'
            '  - All worker slots occupied by slow task\n'
            '  - Fast tasks queued but not executed\n'
            '  - Response times degrade\n'
            '  - Worker appears hung'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Short tasks delayed by long tasks')
        self.stdout.write('  - User-facing requests timeout')
        self.stdout.write('  - Worker becomes unresponsive')
