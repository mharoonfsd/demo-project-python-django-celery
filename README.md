# Django Celery Issues Demo

This project demonstrates common issues that can occur when using Django with Celery, signals, transactions, and AWS services.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start Redis (required for Celery):
```bash
redis-server
```

4. Start Celery worker:
```bash
celery -A demo_project worker -l info
```

## Demonstrated Issues

### Question 1: bulk_create and Signals
**Original Question:**
> **Q:** Why does `bulk_create()` not trigger signals?
> **A:** It bypasses ORM lifecycle.
> **Explanation:** Django executes direct SQL.
> **Fix:** Manually trigger logic or avoid bulk ops for critical flows.

**Issue**: `Order.objects.bulk_create(orders_list)` doesn't trigger `post_save` signals.

**Demo**: Run `python manage.py demo_bulk_create`

**Expected Output**:
- Bulk created orders don't send notification emails
- Regular `save()` does send notifications

### Question 2: Transactions and Celery Tasks
**Original Question:**
> **Q:** You override `save()` and also use signals. Which runs first?
> **A:** `save()` → DB write → signals.
> **Explanation:** Signals run after save lifecycle, causing possible overwrites.

**Issue**: Celery tasks queued from `post_save` signals inside transactions may fail to find the object.

**Demo**: Run `python manage.py demo_transaction`

**Expected Output**:
- Order created successfully
- Celery task may fail in production due to transaction isolation

### Question 3: Celery Retry Behavior
**Original Question:**
> **Q:** Why does `bulk_update()` not trigger signals?
> **A:** It bypasses ORM lifecycle.
> **Explanation:** Django executes direct SQL.
> **Fix:** Manually trigger logic or avoid bulk ops for critical flows.

**Issue**: Understanding how `max_retries=3` works.

**Demo**: Run `python manage.py demo_retry`

**Expected Output**:
- Task executes 4 times total (1 initial + 3 retries)
- Check Celery logs for retry attempts

### Question 4: SNS Duplicate Events
**Original Question:**
> **Q:** CASCADE not working?
> **A:** Raw SQL or DB mismatch.
> **Explanation:** ORM cascade differs from DB constraint.

**Issue**: SNS can deliver events multiple times, causing duplicate processing.

**Demo**: Run `python manage.py demo_sns_duplicates`

**Expected Output**:
- Multiple PDF generation tasks queued for the same event
- Potential duplicate database records and reports

### Question 5: ECS Backpressure
**Original Question:**
> **Q:** `select_related()` but still N+1?
> **A:** Using M2M.
> **Fix:**
> ```python
> Order.objects.prefetch_related('items')
> ```

**Issue**: ECS containers processing large Parquet files face backpressure and restarts.

**Demo**: Run `python manage.py demo_ecs_backpressure`

**Expected Output**:
- Multiple slow tasks queued simultaneously
- Demonstrates memory pressure and processing delays

## API Endpoints

- `POST /orders/create/` - Create single order (with transaction)
- `POST /orders/bulk-import/` - Bulk import from CSV

## Answers to Questions

### Question 1
**How many notifications are sent?** 0

**Why?** `bulk_create()` bypasses the `post_save` signal entirely for performance reasons. Signals are only triggered for individual `save()` calls.

### Question 2
**What's happening?** The `post_save` signal fires immediately when `Order.objects.create()` is called inside the transaction, but the transaction hasn't been committed yet. The Celery task runs in a separate process/database connection that can't see the uncommitted transaction.

**How to fix it:**
1. Move the signal handler outside the transaction
2. Use `transaction.on_commit()` to defer the task until after commit
3. Use database constraints and unique keys to handle duplicates

### Question 3
**How many total times does the task execute?** 4 times (1 initial + 3 retries)

**Reasoning:**
- First execution fails → retry 1
- Second execution fails → retry 2
- Third execution fails → retry 3
- Fourth execution fails → no more retries, task marked as failed

### Question 4
**Root causes:**
1. SNS at-least-once delivery guarantee
2. No deduplication mechanism
3. Tasks are queued asynchronously without checking for existing work

**Complete fix:**
1. Add message deduplication using SNS message ID or custom deduplication key
2. Use Redis or database to track in-progress work
3. Implement idempotent operations
4. Use SQS FIFO queues with deduplication
5. Add database unique constraints

### Question 5
**Problem:** The ECS tasks are processing large datasets sequentially without proper resource management, causing memory exhaustion and container restarts.

**Solution:**
1. Process data in smaller batches
2. Implement proper memory management
3. Use streaming processing instead of loading all data into memory
4. Add circuit breakers and backpressure handling
5. Use SQS batch processing
6. Implement proper error handling and DLQ usage
7. Scale ECS tasks based on queue depth