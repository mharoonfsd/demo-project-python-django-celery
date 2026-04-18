from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q37 PROBLEM: Celery does not guarantee FIFO ordering. Even if tasks are
    enqueued in order 1, 2, 3, they may execute as 3, 1, 2. With multiple
    workers and variable task duration, ordering is unpredictable. This
    breaks business logic that depends on sequencing.
    """
    help = 'Q37 Problem: Tasks execute out-of-order despite FIFO queue'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q37 PROBLEM: Out-of-order task execution')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q37-ORDER',
            customer_email='q37@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}')

        # Simulate task queue
        executed = []

        @app.task
        def step_task(step_num):
            """Steps that must execute in order."""
            executed.append(step_num)
            self.stdout.write(f'  Step {step_num} executed')
            return step_num

        self.stdout.write('\nEnqueuing 5 tasks in order: 1, 2, 3, 4, 5\n')

        self.stdout.write('Enqueued: step_task(1)')
        step_task.delay(1)

        self.stdout.write('Enqueued: step_task(2)')
        step_task.delay(2)

        self.stdout.write('Enqueued: step_task(3)')
        step_task.delay(3)

        self.stdout.write('\nWith multiple workers, they pick up tasks in parallel:')
        self.stdout.write('  Worker-A: grabs task(1) - slow (10s)')
        self.stdout.write('  Worker-B: grabs task(2) - fast (1s) -> completes first')
        self.stdout.write('  Worker-C: grabs task(3) - fast (1s) -> completes second')
        self.stdout.write('  Worker-A: task(1) completes last')
        self.stdout.write('')
        self.stdout.write('  Execution order: 2, 3, 1 (not 1, 2, 3!)')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Tasks executed out-of-order:\n'
            '  Enqueued: 1, 2, 3\n'
            '  Executed: 2, 3, 1 (or any random order)\n'
            'If step 3 depends on step 1, this breaks logic.'
        ))
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - State changes applied in wrong order')
        self.stdout.write('  - Dependent tasks fail with missing prerequisites')
        self.stdout.write('  - Data consistency violated')
