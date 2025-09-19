from main import app
from fastapi import Request
from fastapi.responses import JSONResponse

def exception_to_json_response(exc: Exception, status_code=502) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content = {
            "error": True,
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )

@app.exception_handler(Exception)
def default_exception_handler(req: Request, exc: Exception):
    return exception_to_json_response(exc)
