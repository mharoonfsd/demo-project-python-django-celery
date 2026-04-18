from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q69 SOLUTION: Use SNS FIFO topics for ordered delivery. Apply
    sequence-number validation in consumers. Use last-write-wins with
    timestamps to handle out-of-order delivery gracefully.
    """
    help = 'Q69 Solution: SNS FIFO topic or sequence-aware consumer'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q69 SOLUTION: Ordered SNS delivery strategies')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        order = Order.objects.create(
            order_number='Q69-SOL-ORDER',
            customer_email='q69sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        # Simulate out-of-order messages with sequence numbers
        received = [
            {'seq': 3, 'status': 'shipped', 'order_id': order.pk},
            {'seq': 1, 'status': 'pending', 'order_id': order.pk},
            {'seq': 2, 'status': 'confirmed', 'order_id': order.pk},
        ]

        self.stdout.write('Strategy 1: SNS FIFO topic')
        self.stdout.write('  - Topic name must end in .fifo')
        self.stdout.write('  - Paired with SQS FIFO subscriber')
        self.stdout.write('  - Messages delivered in publish order per MessageGroupId')
        self.stdout.write('  - Limit: 300 publish TPS')
        self.stdout.write('')

        self.stdout.write('Strategy 2: Sequence-aware consumer (standard topic)')
        last_applied_seq = 0
        skipped = []
        applied = []

        for msg in sorted(received, key=lambda m: m['seq']):
            if msg['seq'] <= last_applied_seq:
                skipped.append(msg)
                self.stdout.write(self.style.WARNING(
                    f'  seq={msg["seq"]}: skipped (already applied seq {last_applied_seq})'
                ))
                continue
            last_applied_seq = msg['seq']
            applied.append(msg)
            self.stdout.write(self.style.SUCCESS(
                f'  seq={msg["seq"]}: applied status={msg["status"]}'
            ))

        self.stdout.write('')
        self.stdout.write('Strategy 3: Last-write-wins with timestamp')
        self.stdout.write('  - Store (status, updated_at) in DB')
        self.stdout.write('  - Only update if received timestamp > stored timestamp')
        self.stdout.write('  - Works regardless of arrival order')
        self.stdout.write('  - code: Order.objects.filter(id=id, updated_at__lt=ts).update(status=status)')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - SNS FIFO: strict order, 300 TPS limit')
        self.stdout.write('  - Standard: apply sequence-number validation in consumer')
        self.stdout.write('  - Last-write-wins: idiomatic for status/state updates')
        self.stdout.write('  - Always include seq number + timestamp in events')
