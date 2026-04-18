from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q95 PROBLEM: No data quality checks in pipeline. NULL emails, negative
    amounts, future dates, and wrong types are stored silently. Downstream
    analytics produce nonsensical results.
    """
    help = 'Q95 Problem: No data quality checks - bad data stored silently'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q95 PROBLEM: No data quality checks - garbage in, garbage out')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        from datetime import datetime, timezone, timedelta

        # Bad records that should be caught
        bad_records = [
            {'order_number': 'Q95-GOOD-001', 'customer_email': 'valid@example.com', 'amount': '100.00'},
            {'order_number': 'Q95-NULL-EMAIL', 'customer_email': None, 'amount': '50.00'},
            {'order_number': 'Q95-NEG-AMT', 'customer_email': 'neg@example.com', 'amount': '-200.00'},
            {'order_number': 'Q95-ZERO-AMT', 'customer_email': 'zero@example.com', 'amount': '0.00'},
            {'order_number': 'Q95-NO-AT', 'customer_email': 'notanemail', 'amount': '75.00'},
        ]

        self.stdout.write('Pipeline without data quality checks:')
        stored = 0
        for record in bad_records:
            try:
                email = record['customer_email'] or ''
                Order.objects.create(
                    order_number=record['order_number'],
                    customer_email=email,
                    amount=Decimal(record['amount']),
                    price=Decimal(record['amount']),
                )
                stored += 1
                self.stdout.write(f'  Stored: {record}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  DB error (rare): {e}'))

        self.stdout.write('')
        from django.db.models import Sum, Count
        stats = Order.objects.aggregate(total=Sum('amount'), count=Count('id'))
        self.stdout.write(self.style.ERROR(
            f'Analytics result:'
            f'\n  Total orders: {stats["count"]}'
            f'\n  Total revenue: {stats["total"]}'
            f'\n  Includes: NULL email, -200.00 amount, "notanemail" as customer'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Bad data stored, pollutes all downstream reports'
            '\n  - NULL email: marketing emails fail to send'
            '\n  - Negative amount: revenue report understated'
            '\n  - Invalid email: "notanemail" counted as a customer'
            '\n  - No alert: team discovers problem weeks later in report'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Validate at pipeline entry, not after storing')
        self.stdout.write('  - Define quality rules: not-null, ranges, format patterns')
        self.stdout.write('  - Fail loud: reject bad records to DLQ, alert on volume')
        self.stdout.write('  - Track data quality metrics as pipeline KPIs')
