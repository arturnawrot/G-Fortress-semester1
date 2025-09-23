from main import app
from fastapi import Request, HTTPException
from exceptions.helpers import handle_and_return_exception
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(Exception)
def default_exception_handler(req: Request, exc: Exception):
    return handle_and_return_exception(exc)

# It won't be caught in the default exception handler because it's already targeted by some
# other fastapi exception handler so we need to override it again.
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return handle_and_return_exception(exc, status_code=exc.status_code)

# Same thing as above
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return handle_and_return_exception(exc, status_code=exc.status_code)