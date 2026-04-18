from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q45 PROBLEM: Task name collisions occur when two different tasks
    accidentally have the same name. The wrong task runs, causing data
    corruption or errors.
    """
    help = 'Q45 Problem: Task name collision'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q45 PROBLEM: Task name collision')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        self.stdout.write('Two developers define tasks with same name:')
        self.stdout.write('  module_a.py: @app.task(name="process")')
        self.stdout.write('  module_b.py: @app.task(name="process")')
        self.stdout.write('')
        self.stdout.write('When task "process" is called:')
        self.stdout.write('  - Which implementation runs?')
        self.stdout.write('  - Last registered wins (undefined)')
        self.stdout.write('  - Results in wrong business logic')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Silent, hard-to-debug failures\n'
            '  - Wrong task implementation executes\n'
            '  - Data corruption possible\n'
            '  - No error raised'
        ))
