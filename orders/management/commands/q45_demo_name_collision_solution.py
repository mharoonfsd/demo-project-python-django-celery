from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax
from demo_project.celery import app


class Command(BaseCommand):
    """
    Q45 SOLUTION: Use fully qualified task names (module.task_name) to avoid
    collisions. Or use explicit naming with namespace prefixes.
    """
    help = 'Q45 Solution: Namespaced task names'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q45 SOLUTION: Unique task names')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        # Solution 1: Use module path
        @app.task(name='orders.tasks.process_order')
        def process_order_a(order_id):
            return 'process_a'

        # Solution 2: Use namespace prefix
        @app.task(name='email.send_notification')
        def send_notification(order_id):
            return 'send_notification'

        self.stdout.write('Strategy 1: Fully qualified names')
        self.stdout.write('  @app.task(name="orders.tasks.process_order")')
        self.stdout.write('  @app.task(name="billing.tasks.charge_card")')
        self.stdout.write('')
        self.stdout.write('Strategy 2: Namespace prefixes')
        self.stdout.write('  @app.task(name="orders:process")')
        self.stdout.write('  @app.task(name="billing:charge")')
        self.stdout.write('')
        self.stdout.write('Strategy 3: Auto-naming with app.task')
        self.stdout.write('  Celery auto-generates name from module + function')
        self.stdout.write('  orders.tasks.process_order')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Always use explicit task names')
        self.stdout.write('  - Include namespace/module in name')
        self.stdout.write('  - Use dots (.) for hierarchy')
        self.stdout.write('  - Test task name registry for duplicates')
