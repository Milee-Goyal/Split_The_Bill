import os
import shutil
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.schemas import (
    ParsedBill,
    SplitRequest,
    SplitResponse,
)
from app.calculator import calculate_fair_split
from app.extractor import (
    extract_bill_from_image,
    load_ground_truth_bills,
    get_ground_truth_bill,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEST_BILLS_DIR = os.path.join(BASE_DIR, "test_bills")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEST_BILLS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="Split the Bill From a Photograph",
    description="Intelligent OCR receipt extraction, confidence review, and mathematically fair proportional bill splitting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset folders
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/test_bills", StaticFiles(directory=TEST_BILLS_DIR), name="test_bills")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/")
def get_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Split the Bill API is running. UI index.html not yet installed."}


@app.get("/api/sample-bills")
def list_sample_bills():
    """Returns the list of 12 pre-loaded challenging receipt cases."""
    data = load_ground_truth_bills()
    summaries = []
    for b in data.get("bills", []):
        summaries.append({
            "bill_id": b["bill_id"],
            "bill_name": b["bill_name"],
            "condition_tag": b.get("condition_tag", "Sample"),
            "challenge_description": b.get("challenge_description", ""),
            "image_url": b.get("image_url", ""),
            "items_count": len(b.get("items", [])),
            "grand_total": b.get("metadata", {}).get("grand_total", 0.0),
            "is_arithmetically_valid": b.get("metadata", {}).get("is_arithmetically_valid", True),
        })
    return {"bills": summaries}


@app.get("/api/bills/{bill_id}", response_model=ParsedBill)
def get_bill_detail(bill_id: str):
    bill = get_ground_truth_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@app.post("/api/upload", response_model=ParsedBill)
async def upload_receipt(file: UploadFile = File(...)):
    """Accepts an image file and extracts structured items and totals."""
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4().hex[:10]}{ext}"
    saved_path = os.path.join(UPLOADS_DIR, unique_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with open(saved_path, "rb") as f:
        image_bytes = f.read()

    parsed = extract_bill_from_image(
        image_bytes=image_bytes,
        filename=file.filename,
        content_type=file.content_type or "image/jpeg",
    )
    parsed.image_url = f"/uploads/{unique_filename}"
    return parsed


@app.post("/api/calculate", response_model=SplitResponse)
def calculate_split(request: SplitRequest):
    """Calculates fair-share breakdown with proportional tax distribution."""
    try:
        return calculate_fair_split(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
