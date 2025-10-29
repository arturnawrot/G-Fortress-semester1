from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from db.database import connect_to_db, setup_database
from security.middleware import AESMiddleware
from endpoints import auth as auth_router
from endpoints import user as users_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],   
    allow_headers=['*'],   
)

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
    return {"status": 200}

# @TODO move everything below to a seperate file then apply app.include_router as above
from config import settings
from db.db_service import list_reports
from typing import Literal
import os

@app.get("/report/pdf/{report_id}")
def get_report_as_pdf(report_id: str):
    pdf_file_path = settings.PDF_STORAGE_PATH / f"{report_id}.pdf"
    if not os.path.exists(pdf_file_path):
        return {"error": "PDF file not found"}
    return FileResponse(pdf_file_path, media_type="application/pdf")

@app.get("/reports")
def paginate_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: Literal["newest", "oldest"] = "newest",
):
    order = "DESC" if sort == "newest" else "ASC"
    skip = (page - 1) * page_size

    return list_reports(order, page_size, skip)

# @TODO same thing - move to a seperate file
from typing import List
from db.models import ScheduledScan

@app.post("/scans/scheduled", response_model=ScheduledScan, status_code=201)
async def create_scheduled_scan(scan: ScheduledScan):
    scan.create()
    return scan


@app.get("/scans/scheduled", response_model=List[ScheduledScan])
async def get_scheduled_scans(
    page: int = 0,
    page_size: int = Query(default=10, le=100)
):
    all_scans = ScheduledScan.match_nodes()

    sorted_scans = sorted(all_scans, key=lambda scan: scan.scheduled_at, reverse=True)

    start = (page - 1) * page_size
    end = start + page_size
    return sorted_scans[start:end]