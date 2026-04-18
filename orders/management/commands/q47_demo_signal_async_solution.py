from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q47 SOLUTION: Use transaction.on_commit() to ensure DB is committed
    before enqueueing task. Add error handling and logging in signal handler.
    """
    help = 'Q47 Solution: Proper async handling in signals'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q47 SOLUTION: Safe signal + async pattern')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @receiver(post_save, sender=Order)
        def safe_signal_handler(sender, instance, created, **kwargs):
            """Safe: uses transaction.on_commit()."""
            if created:
                def enqueue_task():
                    try:
                        task_result = send_notification.delay(instance.pk)
                        print(f'Task enqueued: {task_result.id}')
                    except Exception as e:
                        print(f'Failed to enqueue: {e}')
                
                transaction.on_commit(enqueue_task)

        @app.task(bind=True, max_retries=3)
        def send_notification(self, order_id):
            """Async task with retry logic."""
            try:
                order = Order.objects.get(pk=order_id)
                return f'sent to {order.customer_email}'
            except Exception as e:
                raise self.retry(exc=e, countdown=60)

        order = Order.objects.create(
            order_number='Q47-SOL-ORDER',
            customer_email='q47sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Best practice: transaction.on_commit()')
        self.stdout.write('  def safe_handler(sender, instance, created, **kwargs):')
        self.stdout.write('      if created:')
        self.stdout.write('          def enqueue():')
        self.stdout.write('              my_task.delay(instance.pk)')
        self.stdout.write('          transaction.on_commit(enqueue)')
        self.stdout.write('')
        self.stdout.write('Benefits:')
        self.stdout.write('  - DB committed before task enqueue')
        self.stdout.write('  - Task sees fresh data')
        self.stdout.write('  - Error handling in callback')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use transaction.on_commit()')
        self.stdout.write('  - Add try/except in enqueue callback')
        self.stdout.write('  - Task should have max_retries')
        self.stdout.write('  - Log task IDs for debugging')
