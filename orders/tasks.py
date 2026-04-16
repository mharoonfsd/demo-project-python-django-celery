from demo_project.celery import app
import time
import boto3
from django.conf import settings
import httpx
import duckdb
import pyarrow as pa
import pandas as pd
from io import BytesIO


@app.task(bind=True, max_retries=3)
def generate_pdf_report(self, order_id):
    """Simulate generating a large PDF report that takes time"""
    try:
        print(f"Starting PDF generation for order {order_id}")
        # Simulate long-running task (60 minutes)
        time.sleep(2)  # In real scenario, this would be much longer

        # Simulate some processing that might fail
        if self.request.retries > 0:
            raise Exception("Simulated PDF generation failure")

        print(f"PDF report generated for order {order_id}")
        return f"pdf_report_{order_id}.pdf"
    except Exception as exc:
        print(f"Error generating PDF for order {order_id}: {exc}")
        raise self.retry(countdown=60)


@app.task(bind=True)
def process_parquet_to_s3(self, data):
    """Process data and upload Parquet file to S3"""
    try:
        print("Starting Parquet processing...")

        # Simulate slow processing
        time.sleep(5)  # Simulate the 6-hour backpressure

        # Create sample DataFrame
        df = pd.DataFrame(data)

        # Convert to Parquet
        buffer = BytesIO()
        df.to_parquet(buffer, engine='pyarrow')
        buffer.seek(0)

        # Upload to S3 (mock)
        print(f"Uploading Parquet file to S3 with {len(data)} records")

        # In real code:
        # s3_client = boto3.client('s3')
        # s3_client.put_object(Bucket='my-bucket', Key='data.parquet', Body=buffer)

        print("Parquet file uploaded successfully")
        return "success"

    except Exception as exc:
        print(f"Error processing Parquet: {exc}")
        raise


@app.task(bind=True)
def process_sns_event(self, event_data):
    """Process SNS event and queue PDF generation"""
    try:
        print(f"Processing SNS event: {event_data}")

        # Extract order_id from event
        order_id = event_data.get('order_id')

        # Queue the PDF generation task
        generate_pdf_report.delay(order_id)

        print(f"Queued PDF generation for order {order_id}")
        return f"queued_{order_id}"

    except Exception as exc:
        print(f"Error processing SNS event: {exc}")
        raise