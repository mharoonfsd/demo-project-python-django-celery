from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q95 SOLUTION: Validate all records at pipeline entry. Reject bad records
    to a quarantine store. Alert when rejection rate exceeds threshold.
    Track data quality metrics.
    """
    help = 'Q95 Solution: Data quality validation at pipeline entry'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q95 SOLUTION: Data quality validation and quarantine')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        import re

        EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

        def validate_record(record):
            errors = []
            if not record.get('customer_email'):
                errors.append('customer_email is null/empty')
            elif not EMAIL_RE.match(record['customer_email']):
                errors.append(f'customer_email invalid format: {record["customer_email"]}')
            amount = Decimal(str(record.get('amount', '0')))
            if amount <= 0:
                errors.append(f'amount must be > 0, got {amount}')
            if amount > Decimal('100000'):
                errors.append(f'amount suspiciously large: {amount}')
            return errors

        records = [
            {'order_number': 'Q95-SOL-GOOD', 'customer_email': 'valid@example.com', 'amount': '100.00'},
            {'order_number': 'Q95-SOL-NULL', 'customer_email': None, 'amount': '50.00'},
            {'order_number': 'Q95-SOL-NEG', 'customer_email': 'neg@example.com', 'amount': '-200.00'},
            {'order_number': 'Q95-SOL-BADEMAIL', 'customer_email': 'notanemail', 'amount': '75.00'},
            {'order_number': 'Q95-SOL-GOOD2', 'customer_email': 'also@example.com', 'amount': '60.00'},
        ]

        quarantine = []
        accepted = []

        self.stdout.write('Pipeline with data quality validation:')
        for record in records:
            errors = validate_record(record)
            if errors:
                quarantine.append({'record': record, 'errors': errors})
                self.stdout.write(self.style.WARNING(
                    f'  QUARANTINE {record["order_number"]}: {errors}'
                ))
            else:
                accepted.append(record)
                Order.objects.create(
                    order_number=record['order_number'],
                    customer_email=record['customer_email'],
                    amount=Decimal(record['amount']),
                    price=Decimal(record['amount']),
                )
                self.stdout.write(self.style.SUCCESS(
                    f'  ACCEPTED  {record["order_number"]}'
                ))

        rejection_rate = len(quarantine) / len(records) * 100
        ALERT_THRESHOLD = 5.0  # alert if >5% rejected
        self.stdout.write(f'\nData quality summary:')
        self.stdout.write(self.style.SUCCESS(f'  Accepted:  {len(accepted)}/{len(records)}'))
        self.stdout.write(self.style.WARNING(f'  Quarantine: {len(quarantine)}/{len(records)}'))

        if rejection_rate > ALERT_THRESHOLD:
            self.stdout.write(self.style.ERROR(
                f'  ALERT: Rejection rate {rejection_rate:.0f}% > threshold {ALERT_THRESHOLD}%'
                f'\n  -> Send PagerDuty alert / Slack notification'
                f'\n  -> CloudWatch metric: data_quality_rejections'
            ))

        from django.db.models import Sum
        clean_total = Order.objects.aggregate(total=Sum('amount'))['total']
        self.stdout.write(self.style.SUCCESS(
            f'\n  Clean revenue total: {clean_total} (no bad data)'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Validate at entry: fail fast before storing bad data')
        self.stdout.write('  - Quarantine bad records (DLQ or separate table)')
        self.stdout.write('  - Alert when rejection rate exceeds threshold')
        self.stdout.write('  - Track quality metrics: rejection rate, null rate, range violations')
