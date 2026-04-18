from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q11 SOLUTION: Use SELECT ... FOR UPDATE (pessimistic locking) or
    SERIALIZABLE isolation to prevent phantom reads.

    In Django: use queryset.select_for_update() inside an atomic block
    to lock the rows for the duration of the transaction.

    For PostgreSQL SERIALIZABLE isolation, set it per-transaction with
    a raw SQL cursor command.
    """
    help = 'Q11 Solution: Use select_for_update() to prevent phantom reads'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q11 SOLUTION: select_for_update() prevents phantoms')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        Order.objects.create(
            order_number='Q11-SOL-ORDER-1',
            customer_email='q11sol@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )

        self.stdout.write('Transaction A: Read 1 with select_for_update()...')
        with transaction.atomic():
            # SOLUTION: select_for_update locks the rows so concurrent inserts
            # matching the WHERE clause must wait until this TX completes.
            orders = list(Order.objects.select_for_update().all())
            count_first = len(orders)
            self.stdout.write(self.style.SUCCESS(f'  TX-A (locked) sees {count_first} order(s)'))
            self.stdout.write(
                '  Concurrent TX-B cannot insert/modify matching rows until this TX commits.'
            )
            self.stdout.write('  (In this sequential demo the lock is released at the end of this block)')

        self.stdout.write(self.style.SUCCESS('\nPhantom reads prevented for the duration of the transaction.'))
        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - select_for_update() issues SELECT ... FOR UPDATE (PG/MySQL)')
        self.stdout.write('  - Must be inside an atomic() block')
        self.stdout.write('  - For full phantom prevention use SERIALIZABLE isolation in PostgreSQL')
        self.stdout.write('  - SQLite does not support row-level locks; use Postgres in production')
