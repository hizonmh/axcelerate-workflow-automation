"""
Bulk payment recording from CSV — one API transaction per CSV row.
CSV columns: contact_id, date (DD/MM/YYYY), amount, payment_method, reference

contact_id may be:
  - A numeric Axcelerate contactID (e.g. 12000001)
  - An optionalID student code (e.g. MAC0001) — looked up via GET /contacts/search

For each row, the script:
  1. Fetches outstanding invoices for the contact
  2. If exactly one invoice has a balance equal to the payment amount, allocates to it
  3. Otherwise records the payment as unallocated credit

Handles amounts formatted with commas (e.g. "1,000.00").
"""

import csv
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("AXCELERATE_API_TOKEN")
WS_TOKEN  = os.getenv("AXCELERATE_WS_TOKEN")
BASE      = os.getenv("AXCELERATE_BASE_URL")

headers = {"apitoken": API_TOKEN, "wstoken": WS_TOKEN}

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

CSV_PATH = os.path.join(os.path.dirname(__file__), "payments.csv")

transactions = []
failed_count = 0
failed_rows  = []

print(f"Loading payments from: {CSV_PATH}\n")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = [
        {k.strip(): v for k, v in row.items()}
        for row in reader
        if any(v.strip() for v in row.values())
    ]

for row in rows:
    raw_id         = row["contact_id"].strip()
    raw_date       = row["date"].strip()
    raw_amount     = row["amount"].strip().replace(",", "").replace("$", "")
    payment_method = row["payment_method"].strip()
    reference      = row["reference"].strip()

    # Parse DD/MM/YYYY from CSV, send as MM/DD/YYYY (API interprets first value as month)
    dt = datetime.strptime(raw_date, "%d/%m/%Y")
    trans_date = dt.strftime("%m/%d/%Y")

    payment_method_id = METHOD_MAP.get(payment_method.lower(), 4)
    amount = float(raw_amount)

    print(f"Processing {raw_id} | ${raw_amount} | {payment_method} | {reference} | {trans_date}")

    try:
        # Resolve contact_id: numeric = use directly; non-numeric = look up by optionalID
        if raw_id.isdigit():
            contact_id = int(raw_id)
        else:
            search = requests.get(
                f"{BASE}/contacts/search",
                headers=headers,
                params={"optionalID": raw_id}
            )
            search.raise_for_status()
            results = search.json()
            if not results or not isinstance(results, list) or len(results) == 0:
                raise ValueError(f"No contact found for optionalID={raw_id}")
            contact_id = int(results[0]["CONTACTID"])
            print(f"  Resolved {raw_id} -> CONTACTID={contact_id}")

        # Check for a matching invoice (balance == payment amount)
        invoice_id = None
        for status in ["SENT", "PARTIAL", "OVERDUE"]:
            inv_r = requests.get(
                f"{BASE}/accounting/invoice/",
                headers=headers,
                params={"contactID": contact_id, "status": status},
            )
            inv_r.raise_for_status()
            inv_results = inv_r.json()
            if isinstance(inv_results, list):
                for inv in inv_results:
                    if abs(float(inv.get("BALANCE", 0)) - amount) < 0.01:
                        invoice_id = inv["INVOICEID"]
                        break
            if invoice_id:
                break

        # Record payment — allocated if matching invoice found, otherwise unallocated
        post_data = {
            "contactID":       contact_id,
            "amount":          amount,
            "paymentMethodID": payment_method_id,
            "transDate":       trans_date,
            "reference":       reference,
            "description":     reference,
        }
        if invoice_id:
            post_data["invoiceID"] = invoice_id
            print(f"  Matched invoice {invoice_id} (balance=${amount:.2f})")
        else:
            print(f"  No matching invoice — recording as unallocated credit")

        r = requests.post(
            f"{BASE}/accounting/transaction/",
            headers=headers,
            data=post_data,
        )
        r.raise_for_status()
        tx = r.json()

        allocated = "Allocated" if invoice_id else "Unallocated"
        transactions.append({
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
        print(f"    OK — TRANSACTIONID={tx['TRANSACTIONID']} | Amount={tx['AMOUNT']} | {allocated}")

    except requests.exceptions.HTTPError as e:
        body = e.response.text if e.response is not None else "(no body)"
        failed_count += 1
        failed_rows.append({"id": raw_id, "amount": raw_amount, "error": f"{e} | {body}"})
        print(f"  FAILED — {e}")
        print(f"  Response body: {body}")
    except Exception as e:
        failed_count += 1
        failed_rows.append({"id": raw_id, "amount": raw_amount, "error": str(e)})
        print(f"  FAILED — {e}")

# ── SESSION TRANSACTION REPORT ───────────────────────────────────────
print("\n" + "=" * 120)
print("SESSION TRANSACTION REPORT")
print("=" * 120)
print(f"{'#':<4} {'ID':<12} {'Contact ID':<12} {'Amount':>10}  {'Method':<18} {'Tx ID':<12} {'Date':<14} {'Invoice':<12} {'Status'}")
print("-" * 120)
for i, tx in enumerate(transactions, 1):
    print(
        f"{i:<4} {tx['id']:<12} {str(tx['contact_id']):<12} "
        f"${float(tx['amount']):>9.2f}  {tx['method']:<18} {str(tx['tx_id']):<12} "
        f"{tx['date']:<14} {str(tx.get('invoice_id', '')):<12} {tx.get('status', '')}"
    )
print("-" * 120)
total = sum(float(t["amount"]) for t in transactions)
print(f"{'TOTAL':<4} {'':<12} {'':<12} ${total:>9.2f}")

allocated_count = sum(1 for t in transactions if t.get("invoice_id"))
unallocated_count = len(transactions) - allocated_count
print(f"\nSuccessful: {len(transactions)}  |  Failed: {failed_count}")
print(f"Allocated: {allocated_count}  |  Unallocated: {unallocated_count}")

if failed_rows:
    print("\nFailed rows:")
    for fr in failed_rows:
        print(f"  {fr['id']} | ${fr['amount']} — {fr['error']}")

print("=" * 120)

# ── CSV REPORT ──────────────────────────────────────────────────────
report_path = os.path.join(
    os.path.dirname(__file__),
    f"payment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
)

report_fields = [
    "contact_id_input", "contact_id",
    "amount", "payment_method", "transaction_id", "date", "reference",
    "invoice_id", "status", "error",
]

with open(report_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=report_fields)
    writer.writeheader()

    for tx in transactions:
        writer.writerow({
            "contact_id_input": tx["id"],
            "contact_id":       tx["contact_id"],
            "amount":           tx["amount"],
            "payment_method":   tx["method"],
            "transaction_id":   tx["tx_id"],
            "date":             tx["date"],
            "reference":        tx.get("reference", ""),
            "invoice_id":       tx.get("invoice_id", ""),
            "status":           tx.get("status", ""),
            "error":            "",
        })

    for fr in failed_rows:
        writer.writerow({
            "contact_id_input": fr["id"],
            "contact_id":       "",
            "amount":           fr["amount"],
            "payment_method":   "",
            "transaction_id":   "",
            "date":             "",
            "reference":        "",
            "invoice_id":       "",
            "status":           "",
            "error":            fr["error"],
        })

print(f"\nCSV report saved to: {report_path}")
