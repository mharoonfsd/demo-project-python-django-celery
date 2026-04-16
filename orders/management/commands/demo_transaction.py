from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order


class Command(BaseCommand):
    help = 'Demonstrate transaction.atomic() issue with Celery tasks'

    def handle(self, *args, **options):
        self.stdout.write('Creating order inside transaction.atomic()...')

        with transaction.atomic():
            order = Order.objects.create(
                order_number='ORDER-TX',
                customer_email='tx@example.com',
                amount=150.00
            )
            self.stdout.write(self.style.SUCCESS(f'Created order {order.id} inside transaction'))

        self.stdout.write('Transaction committed. Celery task should be queued.')
        self.stdout.write('In production, the task might fail because the transaction')
        self.stdout.write('is not committed when the signal fires and queues the task.')