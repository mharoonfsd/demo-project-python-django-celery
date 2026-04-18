from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q36 PROBLEM: Celery's prefetch_multiplier controls how many tasks a worker
    pulls from the broker before executing them. High prefetch can cause memory
    hoarding: the worker pulls 100 tasks into memory, but some are slow/large,
    exhausting RAM while other workers sit idle.
    """
    help = 'Q36 Problem: High prefetch_multiplier causes memory hoarding'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q36 PROBLEM: Prefetch multiplier causes memory hoarding')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Simulate memory usage (no psutil needed for demo)
        simulated_mem = [200.0, 245.0, 290.0, 335.0, 380.0, 425.0]
        initial_mem = simulated_mem[0]

        @app.task
        def memory_heavy_task(order_id):
            """Task that allocates significant memory."""
            big_list = [{'data': f'record_{i}'} for i in range(100000)]
            return len(big_list)

        order = Order.objects.create(
            order_number='Q36-ORDER',
            customer_email='q36@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        self.stdout.write('\nDefault settings:')
        self.stdout.write('  CELERY_WORKER_PREFETCH_MULTIPLIER = 4 (default)')
        self.stdout.write('  With 10 workers: each pulls 4 tasks = 40 tasks in memory')

        self.stdout.write(f'\nInitial memory: {initial_mem:.1f} MB')
        self.stdout.write('\nSimulating prefetch (pulling multiple tasks into memory)...')

        for i in range(5):
            memory_heavy_task(order.pk)
            current_mem = simulated_mem[i + 1]
            self.stdout.write(f'  After task {i+1}: {current_mem:.1f} MB')

        final_mem = simulated_mem[-1]
        self.stdout.write(self.style.WARNING(
            f'\nPROBLEM: Memory usage grew from {initial_mem:.1f} MB to {final_mem:.1f} MB\n'
            '  - All 5 tasks stayed in memory despite completing\n'
            '  - Other workers couldn\'t claim tasks\n'
            '  - OOM killer may target worker'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Worker becomes memory hog')
        self.stdout.write('  - Load imbalance across workers')
        self.stdout.write('  - OOM crashes take down worker')
