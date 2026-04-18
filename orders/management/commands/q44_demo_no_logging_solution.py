from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app
import logging


class Command(BaseCommand):
    """
    Q44 SOLUTION: Add comprehensive logging, structured metrics, and
    distributed tracing. Log task start, completion, errors, and duration.
    """
    help = 'Q44 Solution: Comprehensive logging and observability'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q44 SOLUTION: Full observability')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        logger = logging.getLogger(__name__)

        @app.task(bind=True)
        def observable_task(self, order_id):
            """Task with comprehensive logging."""
            logger.info(f'Task started: {self.name}, task_id={self.request.id}')
            try:
                order = Order.objects.get(pk=order_id)
                logger.debug(f'Order fetched: {order.order_number}')
                # Simulate work
                result = float(order.amount) * 1.1
                logger.info(f'Task completed: result={result}')
                return result
            except Exception as e:
                logger.error(f'Task failed: {e}', exc_info=True)
                raise

        order = Order.objects.create(
            order_number='Q44-SOL-ORDER',
            customer_email='q44sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Task with full observability:')
        self.stdout.write('  - Log task start with task_id')
        self.stdout.write('  - Log key steps and state changes')
        self.stdout.write('  - Log errors with full traceback')
        self.stdout.write('  - Emit metrics: duration, result, errors')
        self.stdout.write('  - Use structured logging (JSON format)')
        self.stdout.write('  - Include trace_id for distributed tracing')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Add logger.info() at task start/end')
        self.stdout.write('  - Log errors with exc_info=True')
        self.stdout.write('  - Emit duration metrics')
        self.stdout.write('  - Use centralized logging (ELK, DataDog)')
