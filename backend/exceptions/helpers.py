from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from config import settings
import traceback

def handle_and_return_exception(exc: Exception, status_code=500) -> JSONResponse:
    log_exception_to_file(exc)

    return JSONResponse(
        status_code=status_code,
        content = {
            "error": True,
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )

def log_exception_to_file(exc: Exception):
    """Write exception details with a timestamp to a log file using only the Exception object."""
    with open(settings.LOG_FILE_PATH, "a") as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ")
        f.write(f"Uncaught exception ({exc.__class__.__name__}): {exc}\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        f.write("\n" + "-" * 60 + "\n")