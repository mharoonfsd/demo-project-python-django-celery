# Django, Celery, Distributed Systems — Test File (100 Q&A with Deep Explanations & Code)

---

## Section 1: Django ORM, Signals, Transactions

### 1.

**Q:** A `pre_save` signal modifies a field based on another model lookup. Under heavy load, inconsistent values appear. Why?
**A:** Race conditions due to non-atomic read-modify-write.
**Explanation:** Multiple concurrent transactions read the same state, compute new values, and overwrite each other.
**Code:**

```python
@receiver(pre_save, sender=Order)
def update_total(sender, instance, **kwargs):
    instance.total = instance.price + Tax.objects.get(id=1).value
```

**Fix:** Use DB-level atomic updates:

```python
from django.db.models import F
Order.objects.filter(id=instance.id).update(total=F('price') + 5)
```

### 2.

**Q:** You override `save()` and also use signals. Which runs first?
**A:** `save()` → DB write → signals.
**Explanation:** Signals run after save lifecycle, causing possible overwrites.

### 3.

**Q:** Why does `bulk_update()` not trigger signals?
**A:** It bypasses ORM lifecycle.
**Explanation:** Django executes direct SQL.
**Fix:** Manually trigger logic or avoid bulk ops for critical flows.

### 4.

**Q:** CASCADE not working?
**A:** Raw SQL or DB mismatch.
**Explanation:** ORM cascade differs from DB constraint.

### 5.

**Q:** `select_related()` but still N+1?
**A:** Using M2M.
**Fix:**

```python
Order.objects.prefetch_related('items')
```

### 6.

**Q:** Queryset evaluated twice?
**A:** No caching across variables.
**Fix:**

```python
qs = list(Order.objects.all())
```

### 7.

**Q:** `update()` vs `save()`?
**A:** Skips signals and validation.

### 8.

**Q:** `unique_together` fails in prod?
**A:** Race condition.
**Fix:** Add DB constraint + retry logic.

### 9.

**Q:** Nested `atomic()`?
**A:** Uses savepoints.

### 10.

**Q:** `post_delete` silent failure?
**A:** Logging missing.

### 11.

**Q:** Phantom reads?
**A:** Isolation level issue.

### 12.

**Q:** M2M with `bulk_create`?
**A:** Not supported.

### 13.

**Q:** `F()` prevents race?
**A:** Yes, atomic DB ops.

### 14.

**Q:** `auto_now` wrong?
**A:** `update()` bypasses.

### 15.

**Q:** Signal exception?
**A:** Breaks transaction.

### 16.

**Q:** `get_or_create()` race?
**Fix:**

```python
try:
    obj, created = Model.objects.get_or_create(...)
except IntegrityError:
    obj = Model.objects.get(...)
```

### 17.

**Q:** `update_or_create()` duplicates?
**A:** Same race issue.

### 18.

**Q:** Migration fails?
**A:** Data violates schema.

### 19.

**Q:** Connection pooling?
**A:** Per-process.

### 20.

**Q:** Deadlocks?
**Fix:** Consistent lock ordering.

### 21.

**Q:** `refresh_from_db()`?
**A:** Avoid stale data.

### 22–25 (Summary)

* Deferred fields load lazily
* Recursive signals cause loops
* Signals hide business logic

---

## Section 2: Celery

### 26.

**Q:** Task runs twice?
**A:** At-least-once delivery.
**Code:**

```python
@app.task(bind=True, acks_late=True)
def process(self, order_id):
    ...
```

**Fix:** Idempotency key.

### 27.

**Q:** Worker crash mid-task?
**A:** Task requeued.

### 28.

**Q:** `acks_late`?
**A:** Ack after execution.

### 29.

**Q:** `retry()`?

```python
self.retry(countdown=5)
```

### 30.

**Q:** Countdown drift?
**A:** Worker clock differences.

### 31.

**Q:** Time limit?

```python
@app.task(time_limit=30)
```

### 32–33.

**Idempotency:**

```python
if OrderLog.objects.filter(id=task_id).exists(): return
```

### 34.

**Q:** Redis down?
**A:** Broker failure.

### 35.

**Q:** Missing result?
**A:** Backend disabled.

### 36–50 (Key Patterns)**

* Prefetch causes hoarding
* Tasks can run out-of-order
* Version tasks carefully
* Use JSON serialization
* Avoid long blocking tasks

---

## Section 3: SNS/SQS

### 51.

**Q:** Duplicate messages?
**A:** At-least-once delivery.

### 52.

**Q:** Visibility timeout?
**A:** Lock duration.

### 53.

**Q:** Long task duplicates?
**Fix:** Increase timeout.

### 54.

**Q:** No DLQ?
**A:** No failure triggered.

### 55–60.

**Key:**

* SNS retries
* SQS standard unordered
* FIFO ensures order but slower

### Code Example (Consumer)

```python
import boto3
sqs = boto3.client('sqs')

resp = sqs.receive_message(QueueUrl=URL)
for msg in resp.get('Messages', []):
    process(msg)
    sqs.delete_message(QueueUrl=URL, ReceiptHandle=msg['ReceiptHandle'])
```

### 61–70.

**Fix Patterns:**

* Idempotency keys
* DLQ setup
* Long polling

---

## Section 4: ECS / Scaling

### 71.

**Q:** Scaling no help?
**A:** DB bottleneck.

### 72.

**Q:** Backpressure?
**A:** Input > throughput.

### 73–75.

**Failures:**

* OOM kills
* CPU throttling

### 76.

**Q:** Autoscaling worse?
**A:** Amplifies load.

### 77–85.

**Fix Patterns:**

* Metrics (CPU, queue lag)
* Rate limiting
* Circuit breakers

---

## Section 5: Data Pipelines

### 86.

**Q:** Parquet slow?
**A:** Compression + IO.

### Code:

```python
import pyarrow.parquet as pq
pq.write_table(table, 'file.parquet', compression='snappy')
```

### 87.

**Q:** Memory spike?
**Fix:** Batch processing.

### 88.

**Q:** DuckDB perf?

```sql
SELECT * FROM parquet_scan('file.parquet')
```

### 89–100.

**Key Issues:**

* Schema mismatch
* Partial writes
* Small file problem
* Reprocessing duplicates

**Fix Pattern:**

```python
if not already_processed(file_id):
    process()
```

---

## Key Production Principles

1. Idempotency everywhere
2. Assume retries & duplicates
3. Use DB constraints as safety net
4. Observability (logs, metrics)
5. Avoid hidden logic (signals)

---

## End of Test
