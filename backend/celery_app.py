from celery import Celery
from celery.schedules import crontab
from config import settings
from db.database import init_neontology
from db.models import ScheduledScan, ReportNode, CompletedAsRel
from scanner.scanner_service import scan_all_machines
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import redis

# --- New: Initialize Redis Client ---
# Make sure your Redis URL is configured in your settings
redis_client = redis.from_url(settings.CELERY_BROKER_URL)

broker = settings.CELERY_BROKER_URL
backend = settings.CELERY_RESULT_BACKEND

celery_app = Celery("tasks", broker=broker, backend=backend)

# --- New: Lock constants ---
LOCK_PREFIX = "scan_lock:"
LOCK_EXPIRE_SECONDS = 60*10  # 10 minutes


@celery_app.task(name="tasks.run_scheduled_scan")
def run_scheduled_scan(scan_uuid: str):
    lock_key = f"{LOCK_PREFIX}{scan_uuid}"
    try:
        init_neontology()
        scan = ScheduledScan.match(scan_uuid)

        if not scan:
            print(f"Error: ScheduledScan with UUID {scan_uuid} not found.")
            return

        if scan.completed_scan_id:
            print(f"Completed scan_id: {scan.completed_scan_id}")
            print(f"Warning: Scan {scan_uuid} has already been completed. Skipping.")
            return

        try:
            report_id = scan_all_machines()

            # --- FIX 1: Use merge() instead of create() ---
            # This makes the operation idempotent and safe for retries.
            new_report = ReportNode(report_id=report_id)
            new_report.merge()

            # This part is already correct.
            scan.completed_scan_id = report_id
            scan.merge()

            # --- FIX 2: Also use merge() for the relationship ---
            # This is also safer for retries.
            rel = CompletedAsRel(source=scan, target=new_report)
            rel.merge()
            
            print(f"Successfully processed scan {scan_uuid}. Report {report_id} created.")

        except Exception as e:
            print(f"Failed to execute scan {scan_uuid}: {e}")
            if scan.retry_on_fail:
                print("Retrying...")
                raise run_scheduled_scan.retry(exc=e, countdown=60, max_retries=3)
    finally:
        # Releasing the lock is still the correct pattern.
        print(f"Releasing lock for scan {scan_uuid}")
        redis_client.delete(lock_key)

# ... (The schedule_pending_scans task is correct and does not need changes) ...

@celery_app.task(name="tasks.schedule_pending_scans")
def schedule_pending_scans():
    init_neontology()
    
    print("Checking for pending scans...")
    now = datetime.now(ZoneInfo('America/New_York'))

    pending_scans = ScheduledScan.match_nodes(filters={
        "scheduled_at__lte": now,
        "completed_scan_id__isnull": True
    })

    if not pending_scans:
        print("No pending scans found.")
        return

    print(f"Found {len(pending_scans)} scans to run.")
    for scan in pending_scans:
        lock_key = f"{LOCK_PREFIX}{scan.uuid}"
        
        if redis_client.set(lock_key, "locked", ex=LOCK_EXPIRE_SECONDS, nx=True):
            print(f"Lock acquired for scan UUID: {scan.uuid}. Dispatching worker.")
            run_scheduled_scan.delay(scan.uuid)
        else:
            print(f"Scan UUID: {scan.uuid} is already locked. Skipping.")

@celery_app.task(name='tasks.my_task')
def my_task():
    print("Running test task")

celery_app.conf.beat_schedule = {
    "every-minute-task": {
        "task": "tasks.schedule_pending_scans",
        "schedule": crontab(),
    },
    "every-minute-task": {
        "task": "tasks.my_task",
        "schedule": crontab(),
    },
}

celery_app.conf.timezone = "UTC"