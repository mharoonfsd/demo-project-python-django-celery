#!/usr/bin/env python
"""
Test script to trigger the create_order view and hit the breakpoint at line 24
"""
import requests
import json

# Test data for creating an order
import time
order_data = {
    "order_number": f"DEBUG-{int(time.time())}",  # Unique order number
    "customer_email": "debug@example.com",
    "amount": 99.99
}

# Make POST request to create order
url = "http://localhost:8000/orders/create-manual/"
headers = {"Content-Type": "application/json"}

print("Sending POST request to create order...")
print(f"URL: {url}")
print(f"Data: {json.dumps(order_data, indent=2)}")

try:
    response = requests.post(url, json=order_data, headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Connection failed! Make sure Django server is running with debugger.")
    print("Run: F5 or Debug → Django")
except Exception as e:
    print(f"Error: {e}")