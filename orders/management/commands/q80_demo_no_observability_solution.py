from decimal import Decimal
import logging
import json
from django.core.management.base import BaseCommand
from orders.models import Order, Tax


class Command(BaseCommand):
    """
    Q80 SOLUTION: Implement structured logging, custom metrics, and
    distributed tracing. Use correlation IDs to trace requests across services.
    """
    help = 'Q80 Solution: Structured logging, metrics, and tracing'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Q80 SOLUTION: Observability pillars')
        self.stdout.write('='*60)

        Order.objects.all().delete()
        Tax.objects.all().delete()
        Tax.objects.create(name='Standard', value=Decimal('5.00'))
        self.stdout.write('Database truncated.\n')

        for i in range(1, 4):
            Order.objects.create(
                order_number=f'Q80-SOL-{i:03}',
                customer_email=f'q80sol{i}@example.com',
                amount=Decimal('50.00'),
                price=Decimal('50.00'),
            )

        # Pillar 1: Structured Logging
        self.stdout.write('Pillar 1: Structured JSON Logging')
        def structured_log(level, message, **context):
            log_entry = {
                'level': level,
                'message': message,
                'service': 'order-processor',
                **context
            }
            self.stdout.write(f'  LOG: {json.dumps(log_entry)}')

        structured_log('INFO', 'Order processed',
                       order_id=1, duration_ms=45, status='success')
        structured_log('ERROR', 'Payment failed',
                       order_id=2, error='timeout', duration_ms=30000)

        # Pillar 2: Custom Metrics
        self.stdout.write('\nPillar 2: Custom CloudWatch Metrics')
        metrics = {
            'orders_processed': 0,
            'orders_failed': 0,
            'payment_latency_ms': [],
        }

        def record_metric(name, value, unit='Count'):
            metrics[name] = metrics.get(name, 0)
            if isinstance(metrics[name], list):
                metrics[name].append(value)
            else:
                metrics[name] += value
            self.stdout.write(f'  METRIC: {name}={value} ({unit})')

        record_metric('orders_processed', 1)
        record_metric('payment_latency_ms', 45, 'Milliseconds')
        record_metric('orders_failed', 1)

        # Pillar 3: Distributed Tracing
        self.stdout.write('\nPillar 3: Distributed Tracing (X-Ray / OpenTelemetry)')
        self.stdout.write('  from opentelemetry import trace')
        self.stdout.write('  tracer = trace.get_tracer("order-processor")')
        self.stdout.write('  with tracer.start_as_current_span("process_order") as span:')
        self.stdout.write('      span.set_attribute("order.id", order_id)')
        self.stdout.write('      span.set_attribute("order.amount", str(amount))')
        self.stdout.write('      # All nested calls automatically traced')

        self.stdout.write('\nPillar 4: Correlation IDs')
        self.stdout.write('  import uuid')
        self.stdout.write('  correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))')
        self.stdout.write('  # Add to all logs, pass to downstream services')
        self.stdout.write('  # Trace a request across 10 microservices in seconds')

        self.stdout.write('\nKey takeaways:')
        self.stdout.write('  - Structured JSON logs: searchable in CloudWatch Insights')
        self.stdout.write('  - Custom metrics: orders_processed, error_rate, latency p99')
        self.stdout.write('  - Distributed tracing: pinpoint slow spans across services')
        self.stdout.write('  - Correlation ID: stitch together a full request lifecycle')
