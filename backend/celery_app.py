from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init
from config import settings
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import redis

# --- Celery App Setup ---
broker = settings.CELERY_BROKER_URL
backend = settings.CELERY_RESULT_BACKEND
celery_app = Celery("tasks", broker=broker, backend=backend)

# --- Globals for Worker Connections ---
redis_client = None

# --- Lock Constants ---
LOCK_PREFIX = "scan_lock:"
LOCK_EXPIRE_SECONDS = 60 * 10

@worker_process_init.connect
def init_worker(**kwargs):
    """
    Runs ONCE per worker process (after fork). Safe place to init drivers.
    """
    global redis_client
    print("Initializing database and Redis connections for new worker process...")

    # Initialize Neo4j driver here (safe post-fork)
    # IMPORTANT: don't import db/database or db/models until after fork.
    from db.database import init_neontology
    init_neontology(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )

    # Build a fresh Redis client post-fork.
    # (Optionally avoid hiredis to dodge native parser across forks.)
    try:
        from redis.connection import PythonParser
        redis_client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            health_check_interval=30,
            retry_on_timeout=True,
            socket_keepalive=True,
            connection_class=redis.connection.Connection,
            parser_class=PythonParser,  # <- avoids hiredis native parser if installed
        )
    except Exception:
        # Fallback if parser_class arg not supported by your redis-py version
        redis_client = redis.from_url(
            settings.CELERY_BROKER_URL,
            health_check_interval=30,
            retry_on_timeout=True,
            socket_keepalive=True,
        )

    print("Worker initialization complete.")

@celery_app.task(name="tasks.run_scheduled_scan")
def run_scheduled_scan(scan_uuid: str):
    # Lazy imports: ONLY after worker init has happened
    from db.models import ScheduledScan, ReportNode, CompletedAsRel
    from scanner.scanner_service import scan_all_machines

    lock_key = f"{LOCK_PREFIX}{scan_uuid}"
    try:
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

            # Idempotent writes
            new_report = ReportNode(report_id=report_id)
            new_report.merge()

            scan.completed_scan_id = report_id
            scan.merge()

            rel = CompletedAsRel(source=scan, target=new_report)
            rel.merge()

            print(f"Successfully processed scan {scan_uuid}. Report {report_id} created.")

        except Exception as e:
            print(f"Failed to execute scan {scan_uuid}: {e}")
            if getattr(scan, "retry_on_fail", False):
                print("Retrying...")
                raise run_scheduled_scan.retry(exc=e, countdown=60, max_retries=3)
    finally:
        if redis_client:
            print(f"Releasing lock for scan {scan_uuid}")
            try:
                redis_client.delete(lock_key)
            except Exception as e:
                print(f"Warning: failed to release lock for {scan_uuid}: {e}")

@celery_app.task(name="tasks.schedule_pending_scans")
def schedule_pending_scans():
    # Lazy import to ensure graph code only loads post-fork
    from db.models import ScheduledScan

    print("Checking for pending scans...")
    # now = datetime.now(ZoneInfo("America/New_York"))
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

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
        if redis_client and redis_client.set(lock_key, "locked", ex=LOCK_EXPIRE_SECONDS, nx=True):
            print(f"Lock acquired for scan UUID: {scan.uuid}. Dispatching worker.")
            run_scheduled_scan.delay(scan.uuid)
        else:
            print(f"Scan UUID: {scan.uuid} is already locked or Redis unavailable. Skipping.")

@celery_app.task(name='tasks.my_task')
def my_task():
    print("Running test task")

# --- Celery Beat Schedule ---
celery_app.conf.beat_schedule = {
    "schedule_pending_scans_every_minute": {
        "task": "tasks.schedule_pending_scans",
        "schedule": crontab(),
    },
    "my_task_every_minute": {
        "task": "tasks.my_task",
        "schedule": crontab(),
    },
}
celery_app.conf.timezone = "UTC"