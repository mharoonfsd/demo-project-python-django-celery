from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q80 PROBLEM: ECS service has no observability - no structured logging,
    no custom metrics, no distributed tracing. When something goes wrong
    it takes hours to diagnose because there's no data to look at.
    """
    help = 'Q80 Problem: No observability - blind when things break'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q80 PROBLEM: No observability - cannot diagnose failures')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        orders_data = []
        for i in range(1, 4):
            order = Order.objects.create(
                order_number=f'Q80-ORD-{i:03}',
                customer_email=f'q80user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )
            orders_data.append(order)

        def process_order_no_observability(order):
            """Processes order with no logging, metrics, or tracing."""
            try:
                # Business logic
                result = {'status': 'processed', 'order_id': order.pk}
                # No logging of success
                # No metric increment
                # No trace span
                return result
            except Exception as e:
                # No structured error logging
                # No error metric
                # No alert
                print(f'error: {e}')  # useless in production
                return None

        self.stdout.write('Processing orders (no observability):')
        for order in orders_data:
            process_order_no_observability(order)
            self.stdout.write(f'  order {order.pk}: processed (no logs, no metrics)')

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Incident investigation without observability'
            '\n  Q: "Orders are slow - is it DB or payment service?"'
            '\n  A: "We have no idea. No metrics. No traces."'
            '\n'
            '\n  Q: "How many orders failed in the last hour?"'
            '\n  A: "Unknown. We only have a vague error count."'
            '\n'
            '\n  Q: "Which customer was affected?"'
            '\n  A: "We\'d have to search unstructured logs manually."'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Structured JSON logging (not print statements)')
        self.stdout.write('  - Custom CloudWatch metrics (orders_processed, errors)')
        self.stdout.write('  - Distributed tracing (AWS X-Ray / OpenTelemetry)')
        self.stdout.write('  - Dashboards and alerts before incidents happen')
