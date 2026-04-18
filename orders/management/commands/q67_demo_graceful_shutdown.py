from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q67 PROBLEM: ECS consumer containers crash mid-batch without graceful
    shutdown. SIGTERM not handled — process killed immediately. In-flight
    messages not acknowledged, causing duplicate delivery on restart.
    """
    help = 'Q67 Problem: No graceful shutdown - in-flight messages lost/duplicated'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q67 PROBLEM: No graceful shutdown handling')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q67-ORD-{i:03}',
                customer_email=f'q67user{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        in_flight = []
        deleted = []

        def consumer_no_graceful_shutdown():
            """Consumer that ignores SIGTERM and dies mid-batch."""
            batch = [
                {'id': 'msg-1', 'order_id': 1},
                {'id': 'msg-2', 'order_id': 2},
                {'id': 'msg-3', 'order_id': 3},
            ]

            for i, msg in enumerate(batch):
                in_flight.append(msg['id'])
                self.stdout.write(f'  Processing {msg["id"]}...')

                if i == 1:
                    self.stdout.write(self.style.ERROR(
                        '  [SIGTERM received] Container killed immediately!'
                    ))
                    # No cleanup, no ack, process just dies
                    return

                # msg-1 done, delete from SQS
                deleted.append(msg['id'])
                in_flight.remove(msg['id'])
                self.stdout.write(self.style.SUCCESS(f'  {msg["id"]} deleted from queue'))

        consumer_no_graceful_shutdown()

        self.stdout.write(f'\nDeleted from SQS: {deleted}')
        self.stdout.write(self.style.ERROR(
            f'In-flight (NOT deleted): {in_flight}'
        ))
        self.stdout.write(self.style.ERROR(
            '\nPROBLEM:\n'
            '  - msg-2 was being processed when kill arrived\n'
            '  - msg-3 never started\n'
            '  - Both will be redelivered after visibility timeout\n'
            '  - If not idempotent: msg-2 processed twice!'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - ECS sends SIGTERM 30s before SIGKILL (configurable)')
        self.stdout.write('  - Handle SIGTERM: stop accepting new messages')
        self.stdout.write('  - Complete or rollback in-flight messages')
        self.stdout.write('  - Always combine with idempotency (Q51)')
