"""FastAPI backend for the redesigned Bank Transaction Tracker frontend.

Wraps the existing tracker modules:
  - database.py — read/write transactions in tracker.db
  - parsers.py  — detect_and_parse for CSV / Xero / Ezidebit imports
  - bulk_payment.py — invoked as a subprocess for the per-instance upload

Run with:
    uvicorn tracker.api:app --reload --port 8765

Static frontend served from tracker/web/ at /.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database
import parsers

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
PROJECT_ROOT = ROOT.parent
BULK_PAYMENT_SCRIPT = PROJECT_ROOT / "bulk_payment.py"

# Shared metadata so the frontend doesn't have to hardcode it.
STATUSES = [
    {"key": "Unreconciled",       "label": "Unreconciled",       "cls": "unrec"},
    {"key": "OK to Upload",       "label": "OK to Upload",       "cls": "ok"},
    {"key": "Axcelerate Updated", "label": "Axcelerate Updated", "cls": "done"},
    {"key": "Unallocated",        "label": "Unallocated",        "cls": "unalloc"},
    {"key": "Check Manually",     "label": "Check Manually",     "cls": "check"},
    {"key": "No Action",          "label": "No Action",          "cls": "na"},
]
PAYMENT_METHODS = [
    "Direct Deposit", "Agent Deduction", "Direct Debit", "Stripe", "Internal Transfer",
]
INSTANCES = [
    {"code": "MAC",      "name": "MAC",          "cls": "mac"},
    {"code": "NECGC",    "name": "NECGC",        "cls": "necgc"},
    {"code": "NEC",      "name": "NECTECH",      "cls": "nec"},
    {"code": "EZIDEBIT", "name": "MAC-EZIDEBIT", "cls": "ezi"},
]
_VALID_STATUSES = {s["key"] for s in STATUSES}
_VALID_METHODS = set(PAYMENT_METHODS)
_VALID_INSTANCES = {i["code"] for i in INSTANCES}

database.init_db()

app = FastAPI(title="Bank Transaction Tracker API")


# ---------- Schemas ----------

class TxnPatch(BaseModel):
    status: str | None = None
    payment_method: str | None = None
    student: str | None = None


class BulkPatch(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    status: str | None = None
    payment_method: str | None = None
    student: str | None = None


class PrepareUpload(BaseModel):
    upload_amount: float
    upload_description: str


# ---------- Helpers ----------

def _validate_patch(status: str | None, method: str | None) -> None:
    if status is not None and status not in _VALID_STATUSES:
        raise HTTPException(400, f"Unknown status: {status}")
    if method is not None and method not in _VALID_METHODS:
        raise HTTPException(400, f"Unknown payment_method: {method}")


# ---------- API ----------

@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "statuses": STATUSES,
        "payment_methods": PAYMENT_METHODS,
        "instances": INSTANCES,
    }


@app.get("/api/transactions")
def list_transactions() -> list[dict]:
    return database.get_all_transactions()


@app.patch("/api/transactions/{txn_id}")
def patch_transaction(txn_id: int, body: TxnPatch) -> dict:
    _validate_patch(body.status, body.payment_method)
    touched = database.bulk_update_fields(
        [txn_id],
        student=body.student,
        status=body.status,
        payment_method=body.payment_method,
    )
    if touched == 0 and any(v is not None for v in (body.status, body.payment_method, body.student)):
        # Means the row exists but nothing changed — still return current row.
        pass
    return _get_one(txn_id)


@app.post("/api/transactions/bulk")
def bulk_patch(body: BulkPatch) -> dict:
    _validate_patch(body.status, body.payment_method)
    database.bulk_update_fields(
        body.ids,
        student=body.student,
        status=body.status,
        payment_method=body.payment_method,
    )
    return {"updated": len(body.ids)}


@app.post("/api/transactions/{txn_id}/prepare-upload")
def prepare_upload(txn_id: int, body: PrepareUpload) -> dict:
    database.set_upload_amount(txn_id, body.upload_amount, body.upload_description)
    return _get_one(txn_id)


@app.post("/api/import")
async def import_files(files: list[UploadFile] = File(...)) -> dict:
    """Run each uploaded file through the parsers and upsert results.

    Returns a single rolled-up count plus a per-file breakdown so the import
    drawer can show what happened.
    """
    total = {"inserted": 0, "updated": 0, "skipped": 0}
    per_file: list[dict] = []
    errors: list[dict] = []
    for f in files:
        content = await f.read()
        try:
            records = parsers.detect_and_parse(f.filename or "unknown", content)
            counts = database.upsert_transactions(records)
        except Exception as e:
            errors.append({"file": f.filename, "error": str(e)})
            continue
        per_file.append({"file": f.filename, **counts})
        for k in total:
            total[k] += counts[k]
    return {"total": total, "files": per_file, "errors": errors}


@app.post("/api/upload/{instance}")
def upload_to_axcelerate(instance: str) -> dict:
    """Spawn bulk_payment.py for the given instance and return its output.

    Runs synchronously — the frontend shows a spinner while we wait. For long
    batches you'd want SSE or a job queue, but the current Streamlit app calls
    this script the same way and the volumes are small.
    """
    if instance not in _VALID_INSTANCES:
        raise HTTPException(400, f"Unknown instance: {instance}")
    if not BULK_PAYMENT_SCRIPT.exists():
        raise HTTPException(500, f"bulk_payment.py not found at {BULK_PAYMENT_SCRIPT}")
    proc = subprocess.run(
        [sys.executable, str(BULK_PAYMENT_SCRIPT), "--instance", instance],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    return {
        "instance": instance,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


# ---------- Static frontend ----------

def _get_one(txn_id: int) -> dict:
    for r in database.get_all_transactions():
        if r["id"] == txn_id:
            return r
    raise HTTPException(404, f"Transaction {txn_id} not found")


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
