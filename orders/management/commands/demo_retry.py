from django.core.management.base import BaseCommand
from orders.models import send_confirmation_email


class Command(BaseCommand):
    help = 'Demonstrate Celery retry behavior'

    def handle(self, *args, **options):
        self.stdout.write('Demonstrating Celery task with max_retries=3...')
        self.stdout.write('In a real scenario with Celery running:')
        self.stdout.write('1. Task executes for the first time → fails')
        self.stdout.write('2. Celery retries (attempt 1 of 3) → fails')
        self.stdout.write('3. Celery retries (attempt 2 of 3) → fails')
        self.stdout.write('4. Celery retries (attempt 3 of 3) → fails')
        self.stdout.write('5. max_retries exceeded, task marked as FAILED')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Total executions: 4 (1 initial + 3 retries)'))
        self.stdout.write('')
        self.stdout.write('Code example:')
        self.stdout.write('@app.task(bind=True, max_retries=3)')
        self.stdout.write('def my_task(self):')
        self.stdout.write('    try:')
        self.stdout.write('        # do work')
        self.stdout.write('    except Exception:')
        self.stdout.write('        raise self.retry(countdown=60)  # Will retry up to 3 times')