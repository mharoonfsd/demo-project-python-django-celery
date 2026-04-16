from decimal import Decimal

from django.db import models, transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from demo_project.celery import app


class Tax(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Tax {self.name}={self.value}"


class Order(models.Model):
    order_number = models.CharField(max_length=100, unique=True)
    customer_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Check if we should skip signals
        skip_signals = getattr(self, '_skip_signals', False)
        use_safe_calculation = getattr(self, '_use_safe_calculation', False)

        if use_safe_calculation:
            # Safe calculation in save(): calculate total here
            try:
                tax = Tax.objects.get(name='Standard')
                self.total = self.price + tax.value
            except Tax.DoesNotExist:
                self.total = self.price
            # Skip signals
            super().save(*args, **kwargs)
        elif skip_signals:
            # Save without signals
            super().save(*args, **kwargs)
        else:
            # For demo: set custom total if specified
            if hasattr(self, '_custom_total'):
                self.total = self._custom_total
            # Normal save with signals
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"


@receiver(pre_save, sender=Order)
def calculate_order_total(sender, instance, **kwargs):
    # Only calculate if not using safe update
    if getattr(instance, '_use_safe_update', False):
        return

    try:
        tax = Tax.objects.get(name='Standard')
    except Tax.DoesNotExist:
        return

    instance.total = instance.price + tax.value


@app.task(bind=True, max_retries=3)
def send_confirmation_email(self, order_id):
    try:
        order = Order.objects.get(id=order_id)
        # Simulate sending email
        print(f"Sending confirmation email for order {order.order_number}")
        # In real code: send email logic here
    except Order.DoesNotExist:
        print(f"Order {order_id} not found")
        raise self.retry(countdown=60)  # Retry after 1 minute
    except Exception as exc:
        print(f"Error sending email for order {order_id}: {exc}")
        raise self.retry(countdown=60)


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created and not getattr(instance, '_skip_notification', False):
        # FIX: Defer task execution until transaction commits
        def queue_notification():
            try:
                send_confirmation_email.delay(instance.id)
            except Exception as exc:
                # Broker may not be running during local demos.
                print(f"Could not queue Celery task: {exc}")

        transaction.on_commit(queue_notification)
