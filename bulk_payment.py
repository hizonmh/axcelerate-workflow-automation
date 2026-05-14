"""
Bulk payment recording from tracker app — one API transaction per row.

Reads transactions with status "OK to Upload" from the tracker SQLite database.
Field mapping (tracker → Axcelerate):
  student       → contact_id  (numeric ID or MAC optional ID)
  date          → trans_date
  amount        → amount
  payment_method → payment_method_id
  bank_account  → reference

After processing, updates tracker status:
  Allocated   → "Axcelerate Updated"
  Unallocated → "Unallocated"
  Error       → "Check Manually"

Idempotency: a successful POST writes the returned TRANSACTIONID into the
tracker row BEFORE flipping the status. Re-running this script skips any row
that already has axcelerate_transaction_id set, so a network blip after a
successful POST cannot cause a duplicate payment.
"""

import argparse
import csv
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# Reuse the tracker's DB helpers so we have a single source of truth for
# idempotency writes and "check manually" transitions.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tracker"))
from database import record_axcelerate_post, mark_check_manually  # noqa: E402

load_dotenv()

# --- Instance selection ---
parser = argparse.ArgumentParser(description="Bulk payment uploader for Axcelerate")
parser.add_argument("--instance", default="MAC", choices=["MAC", "NECGC", "NEC", "EZIDEBIT"],
                    help="Which Axcelerate instance to upload to (default: MAC)")
args = parser.parse_args()
instance = args.instance

INSTANCE_CREDS = {
    "MAC":      ("AXCELERATE_API_TOKEN", "AXCELERATE_WS_TOKEN", "AXCELERATE_BASE_URL"),
    "NECGC":    ("NECGC_API_TOKEN",     "NECGC_WS_TOKEN",      "NECGC_BASE_URL"),
    "NEC":      ("NEC_API_TOKEN",        "NEC_WS_TOKEN",         "NEC_BASE_URL"),
    "EZIDEBIT": ("AXCELERATE_API_TOKEN", "AXCELERATE_WS_TOKEN", "AXCELERATE_BASE_URL"),
}

token_key, ws_key, url_key = INSTANCE_CREDS[instance]
API_TOKEN = os.getenv(token_key)
WS_TOKEN  = os.getenv(ws_key)
BASE      = os.getenv(url_key)

if not API_TOKEN or not WS_TOKEN or not BASE:
    missing = [k for k, v in [(token_key, API_TOKEN), (ws_key, WS_TOKEN), (url_key, BASE)] if not v]
    print(f"ERROR: Missing required environment variables for instance '{instance}': {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(2)

headers = {"apitoken": API_TOKEN, "wstoken": WS_TOKEN}

# Per-request timeout for every Axcelerate HTTP call. Without this, a hung
# connection would freeze the whole batch until the parent process kills it.
HTTP_TIMEOUT = 30  # seconds

print(f"Instance: {instance}  |  API base: {BASE}")

METHOD_MAP = {
    "cash":             1,
    "credit card":      2,
    "cc":               2,
    "direct deposit":   4,
    "eft":              4,
    "cheque":           5,
    "check":            5,
    "eftpos":           6,
    "bad debt":         8,
    "direct debit":     9,
    "agent deduction":  10,
}

# Regex for valid student identifiers (numeric ID or MAC ID)
MAC_ID_RE = re.compile(r"^MAC\s?\d+$", re.IGNORECASE)

DB_PATH = os.path.join(os.path.dirname(__file__), "tracker", "tracker.db")


def _request_with_retry(method: str, url: str, **kwargs):
    """Wrap requests.request with a small retry on transient failures.

    Retries on connection errors, read timeouts, 429, and 5xx responses
    (with exponential backoff). 4xx other than 429 are not retried — those
    indicate a real client-side problem that won't fix itself.
    """
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    attempts = 3
    backoff = 1.5
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            r = requests.request(method, url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt == attempts:
                raise
            time.sleep(backoff ** attempt)
            continue
        if r.status_code in (429,) or 500 <= r.status_code < 600:
            if attempt == attempts:
                return r  # let caller raise_for_status
            # Honour Retry-After if present, else backoff
            ra = r.headers.get("Retry-After")
            try:
                wait = float(ra) if ra else backoff ** attempt
            except ValueError:
                wait = backoff ** attempt
            time.sleep(wait)
            continue
        return r
    # Unreachable, but satisfies type checkers
    if last_exc:
        raise last_exc
    raise RuntimeError("retry loop exited without result")

# ── LOAD ROWS FROM TRACKER DB ───────────────────────────────────────

print(f"Loading 'OK to Upload' transactions from: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows_raw = conn.execute(
    "SELECT id, student, date, amount, payment_method, bank_account, "
    "       upload_amount, upload_description, axcelerate_transaction_id "
    "FROM transactions "
    "WHERE status = 'OK to Upload' AND instance = ? ORDER BY date",
    (instance,),
).fetchall()
rows = [dict(r) for r in rows_raw]
conn.close()

print(f"Found {len(rows)} {instance} transaction(s) with status 'OK to Upload'\n")

if not rows:
    print("Nothing to process. Exiting.")
    raise SystemExit(0)

# ── PROCESS PAYMENTS ─────────────────────────────────────────────────

transactions = []
failed_count = 0
failed_rows  = []
skipped_rows = []

# Track row_id → new status (used only for the per-instance summary at the end;
# all DB writes happen via record_axcelerate_post / mark_check_manually).
status_updates = {}  # {tracker_row_id: new_status}

for row in rows:
    tracker_id     = row["id"]
    raw_id         = (row["student"] or "").strip()
    raw_date       = (row["date"] or "").strip()
    raw_amount     = str(row["amount"]).strip().replace(",", "").replace("$", "")
    payment_method = (row["payment_method"] or "Direct Deposit").strip()
    reference      = (row["bank_account"] or "").strip()
    existing_tx_id = (row.get("axcelerate_transaction_id") or "").strip()

    # ── IDEMPOTENCY GUARD ──
    # If a previous run already posted this row to Axcelerate (we have the
    # returned TRANSACTIONID), skip it. This prevents duplicate posts when a
    # row was somehow flipped back to "OK to Upload" without clearing the id.
    if existing_tx_id:
        skipped_rows.append({
            "id": tracker_id, "student": raw_id, "amount": raw_amount,
            "reason": f"Already posted to Axcelerate (TRANSACTIONID={existing_tx_id})",
        })
        print(f"SKIP row {tracker_id} | already posted (TRANSACTIONID={existing_tx_id})")
        continue

    # Validate student field — must be numeric ID or MAC ID
    if not raw_id or raw_id == "Unknown":
        skipped_rows.append({"id": tracker_id, "student": raw_id, "amount": raw_amount, "reason": "Empty or Unknown student"})
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"SKIP row {tracker_id} | Student='{raw_id}' — not a valid ID, marking 'Check Manually'")
        continue

    is_numeric = raw_id.isdigit()
    is_mac_id = bool(MAC_ID_RE.match(raw_id))

    if not is_numeric and not is_mac_id:
        skipped_rows.append({"id": tracker_id, "student": raw_id, "amount": raw_amount, "reason": "Student is a name, not a resolvable ID"})
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"SKIP row {tracker_id} | Student='{raw_id}' — not a numeric/MAC ID, marking 'Check Manually'")
        continue

    # Strict date parsing — DB column is canonical YYYY-MM-DD, no fallback.
    # The previous MM/DD/YYYY fallback could silently misinterpret an ambiguous
    # row like '04/05/2026' as April 5 when it meant 4 May.
    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        skipped_rows.append({
            "id": tracker_id, "student": raw_id, "amount": raw_amount,
            "reason": f"Bad date '{raw_date}' (must be YYYY-MM-DD)",
        })
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"SKIP row {tracker_id} | Bad date '{raw_date}' — marking 'Check Manually'")
        continue
    trans_date = dt.strftime("%m/%d/%Y")

    # Strict payment method — silent default to EFT was hiding tracker typos.
    if payment_method.lower() not in METHOD_MAP:
        skipped_rows.append({
            "id": tracker_id, "student": raw_id, "amount": raw_amount,
            "reason": f"Unknown payment method '{payment_method}'",
        })
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"SKIP row {tracker_id} | Unknown payment method '{payment_method}' — marking 'Check Manually'")
        continue
    payment_method_id = METHOD_MAP[payment_method.lower()]
    amount = float(raw_amount)

    # Agent Deduction: use upload_amount (full invoice amount) if set
    upload_amount = row.get("upload_amount")
    upload_desc = row.get("upload_description")
    if upload_amount and payment_method.lower() == "agent deduction":
        api_amount = float(upload_amount)
        description = upload_desc or reference
        print(f"Processing row {tracker_id} | {raw_id} | ${amount:.2f} (upload: ${api_amount:.2f}) | {payment_method} | {reference} | {trans_date}")
    else:
        api_amount = amount
        description = reference
        print(f"Processing row {tracker_id} | {raw_id} | ${amount:.2f} | {payment_method} | {reference} | {trans_date}")

    try:
        # Resolve contact_id: numeric = use directly; MAC ID = look up by optionalID
        if is_numeric:
            contact_id = int(raw_id)
        else:
            search = _request_with_retry(
                "GET",
                f"{BASE}/contacts/search",
                headers=headers,
                params={"optionalID": raw_id},
            )
            search.raise_for_status()
            results = search.json()
            if not results or not isinstance(results, list) or len(results) == 0:
                raise ValueError(f"No contact found for optionalID={raw_id}")
            contact_id = int(results[0]["CONTACTID"])
            print(f"  Resolved {raw_id} -> CONTACTID={contact_id}")

        # ── INVOICE MATCH ──
        # Collect ALL invoices whose balance matches the amount across the open
        # statuses. If multiple match, allocate to the earliest by INVOICEDATE
        # (tie-broken by lowest INVOICEID) — students typically pay oldest
        # outstanding invoices first.
        matches: list[dict] = []
        for status in ["SENT", "PARTIAL", "OVERDUE"]:
            inv_r = _request_with_retry(
                "GET",
                f"{BASE}/accounting/invoice/",
                headers=headers,
                params={"contactID": contact_id, "status": status},
            )
            inv_r.raise_for_status()
            inv_results = inv_r.json()
            if isinstance(inv_results, list):
                for inv in inv_results:
                    try:
                        balance = float(inv.get("BALANCE", 0))
                    except (TypeError, ValueError):
                        continue
                    # Compare in cents to avoid float-equality drift.
                    if round(balance * 100) == round(api_amount * 100):
                        matches.append(inv)

        # De-dup matches by INVOICEID in case the API returned the same invoice
        # under multiple statuses.
        unique_by_id: dict = {}
        for m in matches:
            unique_by_id.setdefault(m.get("INVOICEID"), m)
        matches = list(unique_by_id.values())

        if len(matches) > 1:
            # Sort: earliest INVOICEDATE first, then lowest INVOICEID.
            # Missing/unparseable dates sort last so they don't silently win.
            def _sort_key(inv: dict) -> tuple:
                try:
                    inv_id = int(inv.get("INVOICEID") or 0)
                except (TypeError, ValueError):
                    inv_id = 0
                return (inv.get("INVOICEDATE") or "9999-99-99", inv_id)
            matches.sort(key=_sort_key)
            ids = ", ".join(str(m.get("INVOICEID")) for m in matches)
            chosen = matches[0]
            print(
                f"  Multiple invoices match ${api_amount:.2f} (IDs: {ids}). "
                f"Picking earliest -> INVOICEID={chosen.get('INVOICEID')} "
                f"dated {chosen.get('INVOICEDATE')}."
            )

        invoice_id = matches[0]["INVOICEID"] if matches else None

        # Record payment — allocated if matching invoice found, otherwise unallocated
        post_data = {
            "contactID":       contact_id,
            "amount":          api_amount,
            "paymentMethodID": payment_method_id,
            "transDate":       trans_date,
            "reference":       reference,
            "description":     description,
        }
        if invoice_id:
            post_data["invoiceID"] = invoice_id
            print(f"  Matched invoice {invoice_id} (balance=${api_amount:.2f})")
        else:
            print(f"  No matching invoice — recording as unallocated credit")

        r = _request_with_retry(
            "POST",
            f"{BASE}/accounting/transaction/",
            headers=headers,
            data=post_data,
        )
        r.raise_for_status()
        tx = r.json()

        allocated = "Allocated" if invoice_id else "Unallocated"
        new_status = "Axcelerate Updated" if invoice_id else "Unallocated"

        # Persist the returned TRANSACTIONID *before* flipping status. If the
        # process dies between this write and any subsequent work, the
        # idempotency guard at the top of the loop will skip the row on the
        # next run instead of double-posting.
        record_axcelerate_post(
            row_id=tracker_id,
            transaction_id=str(tx["TRANSACTIONID"]),
            invoice_id=str(invoice_id) if invoice_id else None,
            new_status=new_status,
        )

        transactions.append({
            "tracker_id": tracker_id,
            "id":         raw_id,
            "contact_id": contact_id,
            "amount":     tx["AMOUNT"],
            "method":     payment_method,
            "tx_id":      tx["TRANSACTIONID"],
            "date":       tx["TRANSDATE"],
            "reference":  tx.get("REFERENCE", reference),
            "invoice_id": invoice_id or "",
            "status":     allocated,
        })
        status_updates[tracker_id] = new_status
        print(f"    OK — TRANSACTIONID={tx['TRANSACTIONID']} | Amount={tx['AMOUNT']} | {allocated}")

    except requests.exceptions.HTTPError as e:
        body = e.response.text if e.response is not None else "(no body)"
        failed_count += 1
        failed_rows.append({"tracker_id": tracker_id, "id": raw_id, "amount": raw_amount, "error": f"{e} | {body}"})
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"  FAILED — {e}")
        print(f"  Response body: {body}")
    except Exception as e:
        failed_count += 1
        failed_rows.append({"tracker_id": tracker_id, "id": raw_id, "amount": raw_amount, "error": str(e)})
        mark_check_manually(tracker_id)
        status_updates[tracker_id] = "Check Manually"
        print(f"  FAILED — {e}")

# ── SESSION TRANSACTION REPORT ───────────────────────────────────────
print("\n" + "=" * 130)
print("SESSION TRANSACTION REPORT")
print("=" * 130)
print(f"{'#':<4} {'Row':<6} {'ID':<12} {'Contact ID':<12} {'Amount':>10}  {'Method':<18} {'Tx ID':<12} {'Date':<14} {'Invoice':<12} {'Status'}")
print("-" * 130)
for i, tx in enumerate(transactions, 1):
    print(
        f"{i:<4} {str(tx['tracker_id']):<6} {tx['id']:<12} {str(tx['contact_id']):<12} "
        f"${float(tx['amount']):>9.2f}  {tx['method']:<18} {str(tx['tx_id']):<12} "
        f"{tx['date']:<14} {str(tx.get('invoice_id', '')):<12} {tx.get('status', '')}"
    )
print("-" * 130)
total = sum(float(t["amount"]) for t in transactions)
print(f"{'TOTAL':<4} {'':<6} {'':<12} {'':<12} ${total:>9.2f}")

allocated_count = sum(1 for t in transactions if t.get("invoice_id"))
unallocated_count = len(transactions) - allocated_count
print(f"\nSuccessful: {len(transactions)}  |  Failed: {failed_count}  |  Skipped: {len(skipped_rows)}")
print(f"Allocated: {allocated_count}  |  Unallocated: {unallocated_count}")

if skipped_rows:
    print("\nSkipped rows:")
    for sr in skipped_rows:
        print(f"  Row {sr['id']} | Student='{sr['student']}' | ${sr['amount']} — {sr['reason']}")

if failed_rows:
    print("\nFailed rows (marked 'Check Manually'):")
    for fr in failed_rows:
        print(f"  Row {fr['tracker_id']} | {fr['id']} | ${fr['amount']} — {fr['error']}")

# Status update summary
print("\nTracker status updates:")
status_summary = {}
for new_status in status_updates.values():
    status_summary[new_status] = status_summary.get(new_status, 0) + 1
for s, count in sorted(status_summary.items()):
    print(f"  {s}: {count}")

print("=" * 130)

# ── CSV REPORT (append to persistent per-instance file) ─────────────
report_label = "NECTECH" if instance == "NEC" else instance
report_path = os.path.join(
    os.path.dirname(__file__),
    f"payment_report_{report_label}.csv",
)

report_fields = [
    "uploaded_at", "tracker_row_id", "contact_id_input", "contact_id",
    "amount", "payment_method", "transaction_id", "date", "reference",
    "invoice_id", "status", "tracker_status", "error",
]

write_header = not os.path.exists(report_path)
uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(report_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=report_fields)
    if write_header:
        writer.writeheader()

    for tx in transactions:
        writer.writerow({
            "uploaded_at":      uploaded_at,
            "tracker_row_id":   tx["tracker_id"],
            "contact_id_input": tx["id"],
            "contact_id":       tx["contact_id"],
            "amount":           tx["amount"],
            "payment_method":   tx["method"],
            "transaction_id":   tx["tx_id"],
            "date":             tx["date"],
            "reference":        tx.get("reference", ""),
            "invoice_id":       tx.get("invoice_id", ""),
            "status":           tx.get("status", ""),
            "tracker_status":   status_updates.get(tx["tracker_id"], ""),
            "error":            "",
        })

    for sr in skipped_rows:
        writer.writerow({
            "uploaded_at":      uploaded_at,
            "tracker_row_id":   sr["id"],
            "contact_id_input": sr["student"],
            "contact_id":       "",
            "amount":           sr["amount"],
            "payment_method":   "",
            "transaction_id":   "",
            "date":             "",
            "reference":        "",
            "invoice_id":       "",
            "status":           "Skipped",
            "tracker_status":   status_updates.get(sr["id"], ""),
            "error":            sr["reason"],
        })

    for fr in failed_rows:
        writer.writerow({
            "uploaded_at":      uploaded_at,
            "tracker_row_id":   fr["tracker_id"],
            "contact_id_input": fr["id"],
            "contact_id":       "",
            "amount":           fr["amount"],
            "payment_method":   "",
            "transaction_id":   "",
            "date":             "",
            "reference":        "",
            "invoice_id":       "",
            "status":           "Failed",
            "tracker_status":   "Check Manually",
            "error":            fr["error"],
        })

print(f"\nCSV report appended to: {report_path}")
