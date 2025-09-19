from fastapi import FastAPI
from db.database import connect_to_db, setup_database
from security.middleware import AESMiddleware
from endpoints import auth as auth_router
from endpoints import user as users_router

app = FastAPI()

app.add_middleware(AESMiddleware)

from exceptions.exception_handler import *

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/api/users", tags=["users"])

@app.on_event("startup")
def on_startup():
    connect_to_db()
    setup_database()

@app.get("/")
def main():
    from scanner.scanner_service import scan_all_machines
    scan_all_machines()
    return {"status": 200}