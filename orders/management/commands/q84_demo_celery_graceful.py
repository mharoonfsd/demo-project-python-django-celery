from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q84 PROBLEM: Celery worker on ECS doesn't handle SIGTERM gracefully.
    When ECS stops the task (deploy, scale-in, spot interruption), the worker
    is killed instantly mid-task. Orders are partially processed, DB is in
    inconsistent state, and the task is requeued and processed again (duplicate).
    """
    help = 'Q84 Problem: Celery worker killed mid-task on SIGTERM'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q84 PROBLEM: No graceful shutdown - tasks killed mid-execution')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q84-ORD-{i:03}',
                customer_email=f'q84user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        tasks_in_flight = [
            {'id': 'task-1', 'order': 1, 'step': 'charging_card', 'progress': '50%'},
            {'id': 'task-2', 'order': 2, 'step': 'sending_email', 'progress': '80%'},
            {'id': 'task-3', 'order': 3, 'step': 'updating_inventory', 'progress': '10%'},
        ]

        self.stdout.write('Celery worker state at SIGTERM moment:')
        for t in tasks_in_flight:
            self.stdout.write(f'  {t["id"]}: processing order-{t["order"]}, step={t["step"]} ({t["progress"]})')

        self.stdout.write(self.style.ERROR('\nECS sends SIGTERM (deploy/scale-in)...'))
        self.stdout.write(self.style.ERROR('Worker not catching SIGTERM — using default behavior'))
        self.stdout.write(self.style.ERROR('After stopTimeout (30s): ECS sends SIGKILL'))
        self.stdout.write('')

        outcomes = [
            ('task-1', 'card charged but order NOT marked as paid -> double charge on retry'),
            ('task-2', 'email sent but task ACK not sent -> email sent again on retry'),
            ('task-3', 'inventory lock acquired but not released -> deadlock'),
        ]
        for task_id, outcome in outcomes:
            self.stdout.write(self.style.ERROR(f'  {task_id}: {outcome}'))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: In-flight tasks are corrupted or duplicated'
            '\n  - No chance to finish current unit of work'
            '\n  - No chance to release locks or external resources'
            '\n  - ACK_LATE + lack of idempotency = duplicate processing'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Celery workers must handle SIGTERM for graceful shutdown')
        self.stdout.write('  - Use --without-gossip --without-mingle for faster shutdown')
        self.stdout.write('  - Increase ECS stopTimeout to match max task duration')
        self.stdout.write('  - Make tasks idempotent to handle duplicate execution safely')
