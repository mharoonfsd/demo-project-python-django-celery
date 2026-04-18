from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q24 SOLUTION: Move business logic out of signals into explicit service
    functions. Signals should only handle cross-cutting concerns (audit logs,
    cache invalidation, metrics). The "domain logic" belongs in service functions
    that callers invoke explicitly — making behaviour visible and testable.
    """
    help = 'Q24 Solution: Move business logic to explicit service functions'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q24 SOLUTION: Explicit service functions replace signal logic')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        # Service layer — explicit, visible, testable
        class OrderService:
            @staticmethod
            def create_order(order_number, email, amount):
                """
                All business logic is explicit here.
                Anyone reading this function knows exactly what happens.
                """
                order = Order.objects.create(
                    order_number=order_number,
                    customer_email=email,
                    amount=amount,
                    price=amount,
                )
                # Business logic is explicit — no magic, no signals
                OrderService._send_confirmation_email(order)
                OrderService._apply_new_customer_discount(order)
                OrderService._create_audit_log(order)
                return order

            @staticmethod
            def _send_confirmation_email(order):
                # In production: send actual email
                print(f'    [Service] Email sent to {order.customer_email}')

            @staticmethod
            def _apply_new_customer_discount(order):
                print(f'    [Service] Discount checked for {order.order_number}')

            @staticmethod
            def _create_audit_log(order):
                print(f'    [Service] Audit log created for pk={order.pk}')

        self.stdout.write('Calling OrderService.create_order() — logic is explicit:\n')
        order = OrderService.create_order('Q24-SOL-ORDER-1', 'q24sol@example.com', Decimal('100.00'))
        self.stdout.write(self.style.SUCCESS(f'\nOrder created: {order.order_number}'))

        self.stdout.write('\nNow using .update() — logic still runs because we call the service:')
        Order.objects.filter(pk=order.pk).update(amount=Decimal('200.00'))
        OrderService._create_audit_log(order)   # explicitly called where needed
        self.stdout.write(self.style.SUCCESS('Audit log created explicitly — no silent skip'))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Move domain logic to service functions; keep signals thin')
        self.stdout.write('  - Service functions are easy to unit-test without signal setup')
        self.stdout.write('  - Logic is visible at every call site — no hidden side effects')
        self.stdout.write('  - Signals are appropriate for: cache invalidation, audit logging, metrics')
