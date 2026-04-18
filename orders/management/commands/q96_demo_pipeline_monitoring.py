from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q96 PROBLEM: Pipeline has no monitoring. It runs, produces 0 rows due
    to a filter bug, finishes with exit code 0. No alert. Downstream
    consumers read empty data and report $0 revenue for the day.
    """
    help = 'Q96 Problem: No pipeline monitoring - silent failure produces 0 rows'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q96 PROBLEM: No monitoring - pipeline silently produces 0 rows')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 6):
            Order.objects.create(
                order_number=f'Q96-ORD-{i:03}',
                customer_email=f'q96user{i}@example.com',
                amount=Decimal('100.00'),
                price=Decimal('100.00'),
            )

        def buggy_pipeline():
            """Bug: filters by wrong date range, returns 0 rows."""
            # BUG: wrong year in filter - no rows match
            from datetime import date
            orders = list(
                Order.objects.filter(
                    created_at__date=date(1999, 1, 1)  # BUG: wrong year
                ).values('id', 'amount')
            )
            output = []
            for order in orders:
                output.append({'id': order['id'], 'amount': str(order['amount'])})
            return output

        self.stdout.write('Running pipeline (with silent bug)...')
        result = buggy_pipeline()

        self.stdout.write(f'Pipeline finished. Output: {len(result)} rows')
        self.stdout.write(f'Exit code: 0 (success)')
        self.stdout.write(self.style.ERROR(
            '\n  NO ALERT. No one noticed.'
            '\n  Downstream report: Revenue today = $0'
            '\n  Actual orders in DB: 5'
            '\n  Team discovers issue 24 hours later when CFO asks why revenue = $0'
        ))

        self.stdout.write(self.style.ERROR(
            '\nPROBLEM: Pipeline with 0-row output exits cleanly'
            '\n  - No row count check or minimum threshold'
            '\n  - No comparison to historical baselines'
            '\n  - No alert on anomalous output'
            '\n  - CloudWatch shows "pipeline: SUCCESS" — misleading'
        ))

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Assert output row count > 0 (or > MIN_EXPECTED)')
        self.stdout.write('  - Compare to previous run: > 50% drop = alert')
        self.stdout.write('  - Emit row_count metric to CloudWatch after every run')
        self.stdout.write('  - Alarm if row_count < threshold or duration > max')
