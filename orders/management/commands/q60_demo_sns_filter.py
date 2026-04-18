from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q60 PROBLEM: SNS subscription filter policies not configured. All
    subscribers receive all messages regardless of type. High-volume
    unrelated messages overwhelm specialized consumers.
    """
    help = 'Q60 Problem: No SNS subscription filter - all messages to all subscribers'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q60 PROBLEM: SNS subscription - no message filtering')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        Order.objects.create(
            order_number='Q60-ORDER',
            customer_email='q60@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # All events published to one SNS topic
        events = [
            {'event_type': 'order_created', 'order_id': 1},
            {'event_type': 'payment_captured', 'order_id': 1},
            {'event_type': 'order_shipped', 'order_id': 1},
            {'event_type': 'order_created', 'order_id': 2},
            {'event_type': 'inventory_updated', 'product_id': 5},
            {'event_type': 'inventory_updated', 'product_id': 6},
        ]

        # Subscribers: email-service only cares about order_created
        #              shipping-service only cares about payment_captured
        # But without filter policy, both receive EVERYTHING

        def email_service_no_filter(event):
            """Email service processes ALL events (wasteful)."""
            if event['event_type'] != 'order_created':
                return 'ignored_but_still_invoked'
            return 'sent_email'

        def shipping_service_no_filter(event):
            """Shipping service processes ALL events (wasteful)."""
            if event['event_type'] != 'payment_captured':
                return 'ignored_but_still_invoked'
            return 'scheduled_shipment'

        total_invocations = 0
        useful_invocations = 0

        self.stdout.write('Events received by each subscriber (no filter):')
        for event in events:
            total_invocations += 2  # both services invoked
            r1 = email_service_no_filter(event)
            r2 = shipping_service_no_filter(event)
            if 'ignored' not in r1:
                useful_invocations += 1
            if 'ignored' not in r2:
                useful_invocations += 1
            self.stdout.write(
                f'  {event["event_type"]}: email={r1}, shipping={r2}'
            )

        efficiency = (useful_invocations / total_invocations) * 100
        self.stdout.write(self.style.ERROR(
            f'\nPROBLEM: {total_invocations} Lambda invocations for {len(events)} events'
            f'\n  Useful work: {useful_invocations}/{total_invocations} ({efficiency:.0f}%)'
            f'\n  Lambda cost wasted on useless invocations'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Without filter policy, all subscribers receive all messages')
        self.stdout.write('  - Wastes Lambda invocations, SQS processing, compute time')
        self.stdout.write('  - Add FilterPolicy to SNS subscriptions')
        self.stdout.write('  - Filter on message attributes (event_type, region, etc.)')
