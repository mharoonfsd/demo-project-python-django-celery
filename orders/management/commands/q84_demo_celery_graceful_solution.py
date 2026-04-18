from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q84 SOLUTION: Configure Celery for graceful shutdown on SIGTERM.
    Set ECS stopTimeout > max task duration. Use REVOKING to cancel
    reserved tasks. Make tasks idempotent so retries are safe.
    """
    help = 'Q84 Solution: Graceful Celery shutdown on ECS SIGTERM'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q84 SOLUTION: Graceful Celery worker shutdown')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q84-SOL-{i:03}',
                customer_email=f'q84sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        self.stdout.write('Graceful shutdown sequence on SIGTERM:')
        shutdown_steps = [
            ('t=0s',   'ECS sends SIGTERM to Celery worker'),
            ('t=0s',   'Celery receives SIGTERM -> enters warm shutdown'),
            ('t=0s',   'Worker stops consuming new tasks from queue'),
            ('t=0-60s','In-flight tasks finish their current execution'),
            ('t=60s',  'All tasks complete -> worker exits cleanly with code 0'),
            ('t=60s',  'ECS sees exit code 0 -> task stopped successfully'),
        ]
        for ts, step in shutdown_steps:
            self.stdout.write(self.style.SUCCESS(f'  {ts:8s}: {step}'))

        self.stdout.write('\nCelery worker command (Dockerfile/ECS task definition):')
        self.stdout.write('  celery -A demo_project worker \\')
        self.stdout.write('    --loglevel=info \\')
        self.stdout.write('    --concurrency=4 \\')
        self.stdout.write('    --without-gossip \\')
        self.stdout.write('    --without-mingle \\')
        self.stdout.write('    --without-heartbeat')
        self.stdout.write('  # --without-* flags speed up shutdown (no gossip to flush)')

        self.stdout.write('\nECS task definition stopTimeout:')
        self.stdout.write('  "stopTimeout": 120  // 2 minutes > max task duration')
        self.stdout.write('  # Default is 30s — too short for many tasks')

        self.stdout.write('\nCelery settings (settings.py):')
        self.stdout.write('  CELERY_TASK_ACKS_LATE = True  # ACK only after completion')
        self.stdout.write('  CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Reduce in-flight tasks')
        self.stdout.write('  CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Requeue on crash')

        self.stdout.write('\nIdempotency (safe to retry):')
        self.stdout.write('  @app.task')
        self.stdout.write('  def process_order(order_id):')
        self.stdout.write('      order = Order.objects.get(pk=order_id)')
        self.stdout.write('      if order.status == "processed":')
        self.stdout.write('          return  # Already done, skip safely')
        self.stdout.write('      # ... do work ...')
        self.stdout.write('      Order.objects.filter(pk=order_id).update(status="processed")')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SIGTERM -> Celery warm shutdown (finish current tasks)')
        self.stdout.write('  - stopTimeout must exceed max task duration (add buffer)')
        self.stdout.write('  - ACKS_LATE + REJECT_ON_WORKER_LOST = safe crash recovery')
        self.stdout.write('  - Idempotent tasks = retries are always safe')
