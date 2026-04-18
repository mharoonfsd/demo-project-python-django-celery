from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q24 PROBLEM: Burying business logic inside Django signals makes the
    codebase hard to understand, test, and debug. Callers cannot see what
    will happen when they save a model. The logic is invisible and implicit.

    Side effects vary depending on HOW the model is saved (.save() vs
    .update() vs bulk_create), leading to inconsistent behaviour.
    """
    help = 'Q24 Problem: Business logic hidden in signals is invisible and hard to test'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q24 PROBLEM: Hidden business logic in signals')
        self.stdout.write('='*60)

        # --- clean slate ---
        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated for clean demo.\n')

        side_effects_log = []

        def hidden_business_logic(sender, instance, created, **kwargs):
            """
            All this logic is invisible to whoever calls Order.save().
            They have no idea:
              - An email is being sent
              - A discount is being applied
              - An audit log entry is created
            """
            side_effects_log.append(f'email sent to {instance.customer_email}')
            side_effects_log.append(f'discount applied to order {instance.order_number}')
            side_effects_log.append(f'audit log created for pk={instance.pk}')
            # Worse: this logic doesn't run if someone uses .update() instead of .save()

        post_save.connect(hidden_business_logic, sender=Order, weak=False)

        self.stdout.write('Calling Order.objects.create() ...')
        order = Order.objects.create(
            order_number='Q24-ORDER-1',
            customer_email='q24@example.com',
            amount=Decimal('100.00'),
            price=Decimal('100.00'),
        )
        self.stdout.write(f'Order created: {order.order_number}')
        self.stdout.write(f'Side effects that happened invisibly: {side_effects_log}')

        side_effects_log.clear()
        self.stdout.write('\nNow using .update() instead of .save()...')
        Order.objects.filter(pk=order.pk).update(amount=Decimal('200.00'))
        self.stdout.write(self.style.ERROR(
            f'PROBLEM: Side effects that ran: {side_effects_log} (NONE — logic silently skipped!)'
        ))

        post_save.disconnect(hidden_business_logic, sender=Order)
        self.stdout.write('\nWhy this is dangerous:')
        self.stdout.write('  - Business logic runs inconsistently depending on save method used')
        self.stdout.write('  - Developers reading the call site have no idea what happens')
        self.stdout.write('  - Unit testing requires full signal infrastructure to be set up')
        self.stdout.write('  - Debugging requires knowing all connected signal handlers')
