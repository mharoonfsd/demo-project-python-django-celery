from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q37 SOLUTION: If ordering is critical, use Celery chaining or callbacks.
    Alternatively, use a FIFO queue (SQS FIFO, or RabbitMQ priority queues).
    Or, design tasks to be independent and tolerate reordering.
    """
    help = 'Q37 Solution: Task chaining for ordered execution'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q37 SOLUTION: Task chaining ensures order')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q37-SOL-ORDER',
            customer_email='q37sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Created order pk={order.pk}\n')

        executed_order = []

        @app.task
        def step_1(order_id):
            executed_order.append(1)
            self.stdout.write('  Step 1: Create order draft')
            return order_id

        @app.task
        def step_2(order_id):
            executed_order.append(2)
            self.stdout.write('  Step 2: Process payment')
            return order_id

        @app.task
        def step_3(order_id):
            executed_order.append(3)
            self.stdout.write('  Step 3: Ship order')
            return order_id

        self.stdout.write('Using Celery chain for ordered execution:')
        from celery import chain
        workflow = chain(
            step_1.s(order.pk),
            step_2.s(),
            step_3.s()
        )
        self.stdout.write('Executing chain: step_1 | step_2 | step_3')
        result = workflow.apply_async()
        self.stdout.write(f'Chain submitted with ID: {result.id}')

        self.stdout.write('\nExecution guarantee:')
        self.stdout.write('  - step_1 always runs first')
        self.stdout.write('  - step_2 waits for step_1 result')
        self.stdout.write('  - step_3 waits for step_2 result')
        self.stdout.write(f'\nExecution order: {executed_order}')

        self.stdout.write('\nAlternatives:')
        self.stdout.write('  1. Use RabbitMQ FIFO queue (routing_key per order)')
        self.stdout.write('  2. Use SQS FIFO queue for strict ordering')
        self.stdout.write('  3. Design for idempotence + out-of-order handling')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Use chain() for sequential tasks')
        self.stdout.write('  - Use group() for parallel tasks')
        self.stdout.write('  - Use chord() for map-reduce patterns')
        self.stdout.write('  - Or use FIFO queue if order is critical')
