from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('create-manual/', views.create_order_manual_signal, name='create_order_manual'),
    path('bulk-import/', views.bulk_import_orders, name='bulk_import_orders'),
]