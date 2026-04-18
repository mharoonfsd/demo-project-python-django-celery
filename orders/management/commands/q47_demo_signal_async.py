from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q47 PROBLEM: Django signals are synchronous, but Celery tasks are
    asynchronous. Calling async code from signal handlers causes issues:
    race conditions, lack of error handling, no retry logic.
    """
    help = 'Q47 Problem: Signals calling async code incorrectly'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q47 PROBLEM: Signals + async mismatch')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        @receiver(post_save, sender=Order)
        def risky_signal_handler(sender, instance, created, **kwargs):
            """Risky: calls task with no error handling."""
            if created:
                # Task enqueued but signal continues immediately
                # If task fails, signal doesn't know or retry
                task_result = send_notification.delay(instance.pk)
                # What if task fails? Signal already returned success.

        @app.task
        def send_notification(order_id):
            """Async task that might fail."""
            return 'sent'

        order = Order.objects.create(
            order_number='Q47-ORDER',
            customer_email='q47@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Common issue:')
        self.stdout.write('  Signal fires on post_save')
        self.stdout.write('  Signal calls task.delay()')
        self.stdout.write('  Signal returns immediately')
        self.stdout.write('')
        self.stdout.write('What goes wrong:')
        self.stdout.write('  1. Task enqueue fails (broker down) -> signal succeeds')
        self.stdout.write('  2. Task runs but fails -> silent failure')
        self.stdout.write('  3. Race condition: DB not yet committed')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: No error handling/retry\n'
            '  - Tasks fail silently\n'
            '  - No visibility of failures\n'
            '  - No retry mechanism'
        ))
