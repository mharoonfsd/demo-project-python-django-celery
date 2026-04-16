from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import csv
import io
from .models import Order
from django.db.models.signals import post_save


@csrf_exempt
@require_POST
def create_order(request):
    """Create a single order inside a transaction - PROBLEMATIC VERSION"""
    data = json.loads(request.body)
    with transaction.atomic():
        order = Order.objects.create(
            order_number=data['order_number'],
            customer_email=data['customer_email'],
            amount=data['amount']
        )
        # The post_save signal fires here and queues the Celery task BEFORE commit!
    return JsonResponse({'id': order.id, 'order_number': order.order_number}, status=201)


@csrf_exempt
@require_POST
def create_order_manual_signal(request):
    """Create order with manual signal control - disconnect/reconnect approach"""
    data = json.loads(request.body)
    
    # Disconnect the signal to prevent it from firing during save
    from . import models
    post_save.disconnect(models.send_order_notification, sender=Order)
    
    try:
        with transaction.atomic():
            order = Order.objects.create(
                order_number=data['order_number'],
                customer_email=data['customer_email'],
                amount=data['amount']
            )
        
        # Transaction committed, now manually trigger the notification
        # Since we're outside transaction, queue the task directly
        from .models import send_confirmation_email
        send_confirmation_email.delay(order.id)
        
    finally:
        # Always reconnect the signal
        post_save.connect(models.send_order_notification, sender=Order)
    
    return JsonResponse({'id': order.id, 'order_number': order.order_number}, status=201)


@csrf_exempt
@require_POST
def bulk_import_orders(request):
    """Bulk import orders from CSV - demonstrates the signal issue"""
    csv_data = request.FILES['csv_file'].read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))

    orders_list = []
    for row in csv_reader:
        orders_list.append(Order(
            order_number=row['order_number'],
            customer_email=row['customer_email'],
            amount=row['amount']
        ))

    # This will NOT trigger post_save signals
    Order.objects.bulk_create(orders_list)

    return JsonResponse({'imported': len(orders_list)}, status=201)
