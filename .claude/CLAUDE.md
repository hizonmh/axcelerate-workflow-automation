# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **Claude AI command library, MCP server, and automation toolkit** for managing workflows against the **Axcelerate training management system** REST API. It supports **three Axcelerate instances** (MAC, NECGC, NECTECH) across multiple colleges. It contains:

- **Claude Code skills** (prompt commands) for each API domain
- A **Model Context Protocol (MCP) server** exposing Axcelerate API as tools for any MCP-compatible client
- A **Bank Transaction Tracker** (Streamlit web app, with an optional FastAPI + React redesign) for importing, reconciling, and managing bank transactions across all three instances
- A **Bulk Payment Uploader** script that reads reconciled transactions from the tracker and records them in the correct Axcelerate instance
- A **Reconciliation Engine** that auto-classifies bank transactions by student and payment method

## Repository Structure

- `.claude/axcelerate_api_reference.md` — Full API reference (68KB). Always consult this first when looking up endpoint paths, parameters, and response shapes.
- `.claude/commands/*.md` — Nine modular Claude commands, each scoped to one API domain. These are the skills invoked via `/axcelerate-*` commands.
- `.claude/settings.local.json` — Restricts `WebFetch` to `app.axcelerate.com` and `developer.axcelerate.com` only.
- `axcelerate-mcp-server/` — MCP server exposing Axcelerate API as tools (see below).
- `tracker/` — Bank Transaction Tracker app (see below).
- `bulk_payment.py` — Bulk payment uploader script (see below).
- `.mcp.json` — Project-level MCP server registration for Claude Code.
- `.env` — API tokens for all three instances (gitignored, never committed)
- `payments/` — Operational payment data (gitignored, never committed)
- `legacy payments/` — Legacy per-instance bulk payment scripts (gitignored, never committed)

## Command Files and Their Domains

| Command | Domain |
|---|---|
| `axcelerate-workflow.md` | Master orchestrator — chains multiple commands together |
| `axcelerate-contact.md` | Contact CRUD, search, notes, USI, certificates |
| `axcelerate-course.md` | Course and instance discovery, updates |
| `axcelerate-enrol.md` | Enrolments, bulk enrolment, attendance |
| `axcelerate-invoice.md` | Invoices, credit notes, catalogue items |
| `axcelerate-payment.md` | Payments, refunds, payment links |
| `axcelerate-reconcile.md` | Bank CSV reconciliation — student ID + payment method extraction |
| `axcelerate-email.md` | Template-based email sending |
| `axcelerate-report.md` | Report discovery, running, CSV export |

## API Authentication Pattern

All generated Python code loads credentials from a `.env` file using `python-dotenv`. The system supports **three Axcelerate instances**, each with its own API tokens and base URL:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# MAC instance (default)
API_TOKEN = os.getenv("AXCELERATE_API_TOKEN")
WS_TOKEN  = os.getenv("AXCELERATE_WS_TOKEN")
BASE_URL  = os.getenv("AXCELERATE_BASE_URL")

# NECGC instance
NECGC_API_TOKEN = os.getenv("NECGC_API_TOKEN")
NECGC_WS_TOKEN  = os.getenv("NECGC_WS_TOKEN")
NECGC_BASE_URL  = os.getenv("NECGC_BASE_URL")

# NECTECH instance (env prefix: NEC_)
NEC_API_TOKEN = os.getenv("NEC_API_TOKEN")
NEC_WS_TOKEN  = os.getenv("NEC_WS_TOKEN")
NEC_BASE_URL  = os.getenv("NEC_BASE_URL")

headers = {
    "apitoken": API_TOKEN,
    "wstoken": WS_TOKEN,
}
```

### Instance Credential Mapping

| Instance | Display Label | API Token Env Var | WS Token Env Var | Base URL Env Var |
|----------|---------------|-------------------|------------------|------------------|
| MAC | MAC | `AXCELERATE_API_TOKEN` | `AXCELERATE_WS_TOKEN` | `AXCELERATE_BASE_URL` |
| NECGC | NECGC | `NECGC_API_TOKEN` | `NECGC_WS_TOKEN` | `NECGC_BASE_URL` |
| NEC | NECTECH | `NEC_API_TOKEN` | `NEC_WS_TOKEN` | `NEC_BASE_URL` |

Both tokens come from the Axcelerate admin panel. The base URL is instance-specific (each organisation has its own subdomain). Use `<PLACEHOLDER>` in generated code for any value the user must supply. **Never hardcode tokens or base URLs in scripts.**

## Key API Conventions

- **POST encoding**: All `POST` and `PUT` requests must use **form encoding** (`data=`), NOT JSON (`json=`). Using JSON will silently fail or return incorrect defaults.
- **Date format**: `DD/MM/YYYY` for most endpoints, but `transDate` on payment transactions uses `MM/DD/YYYY`. Some endpoints accept `YYYY-MM-DD` — verify in `.claude/axcelerate_api_reference.md`
- **Error responses** include `error`, `code`, `messages`, and `details` fields; always call `raise_for_status()` in generated scripts
- **IDs are numeric** except invoice GUIDs which are string UUIDs
- **Pagination**: Reports and searches may return paginated results; use `page` and `perpage` parameters

## Standard Python Helper Pattern

The `axcelerate-workflow.md` defines the canonical `AxcelerateClient` class. Use this as the base for all multi-step workflow scripts:

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class AxcelerateClient:
    def __init__(self):
        self.base_url = os.getenv("AXCELERATE_BASE_URL")
        self.headers = {
            "apitoken": os.getenv("AXCELERATE_API_TOKEN"),
            "wstoken": os.getenv("AXCELERATE_WS_TOKEN"),
        }

    def get(self, path, params=None):
        r = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path, data=None):
        r = requests.post(f"{self.base_url}{path}", headers=self.headers, data=data)
        r.raise_for_status()
        return r.json()

    def put(self, path, data=None):
        r = requests.put(f"{self.base_url}{path}", headers=self.headers, data=data)
        r.raise_for_status()
        return r.json()
```

## Typical Workflow Dependency Chain

Operations must be chained in this order when composing multi-step workflows:

1. **Contact** → get/create → yields `CONTACTID`
2. **Course Instance** → search → yields `INSTANCEID`
3. **Enrolment** → create → yields `LEARNERID`
4. **Invoice** → create/get → yields `INVOICEID` / `invoiceGUID`
5. **Payment** → record → yields `TRANSACTIONID`
6. **Email** → send with merge fields from all prior IDs

## MCP Server

The `axcelerate-mcp-server/` directory contains a Python MCP server built with FastMCP that exposes 30+ Axcelerate API operations as tools.

### Setup

```bash
pip install mcp httpx python-dotenv
```

### Registration

The server is registered via `.mcp.json` at the project root. Claude Code picks this up automatically. You can also register manually:

```bash
claude mcp add axcelerate -- python axcelerate-mcp-server/server.py
```

### Architecture

- **`server.py`** — Single-file server using `mcp.server.fastmcp.FastMCP` with STDIO transport
- **`requirements.txt`** — Dependencies: `mcp`, `httpx`, `python-dotenv`
- Uses `httpx.AsyncClient` for async HTTP requests
- All POST/PUT use form encoding (`data=`), consistent with the API conventions above
- Reads credentials from `.env` (currently configured for MAC instance: `AXCELERATE_API_TOKEN`, `AXCELERATE_WS_TOKEN`, `AXCELERATE_BASE_URL`)

### Tool Domains

| Domain | Tools | Examples |
|--------|-------|---------|
| Contact | 7 | `create_contact`, `search_contacts`, `verify_usi` |
| Course | 5 | `list_courses`, `search_instances`, `get_instance_detail` |
| Enrolment | 4 | `enrol_contact`, `bulk_enrol`, `update_enrolment` |
| Invoice | 6 | `create_invoice`, `approve_invoice`, `void_invoice` |
| Payment | 3 | `record_payment`, `list_transactions`, `verify_payment` |
| Email | 1 | `send_template_email` |
| Report | 5 | `run_report`, `run_saved_report`, `list_saved_reports` |
| Catalogue | 2 | `list_catalogue_items`, `get_catalogue_item` |
| Credit Note | 2 | `create_credit_note`, `list_credit_notes` |

### Resource

- `axcelerate://api-reference` — Exposes the full API reference markdown as a readable MCP resource

## Bank Transaction Tracker

The `tracker/` directory contains a Streamlit web app for importing, reconciling, and managing bank transactions before uploading them to Axcelerate, plus an optional FastAPI + React redesign that shares the same SQLite DB and reconciliation modules. It supports **three Axcelerate instances** (MAC, NECGC, NECTECH) with 7 tabs (Received/Spent per instance + MAC-EZIDEBIT for direct debit payments).

### Components

| File | Purpose |
|------|---------|
| `tracker/app.py` | Streamlit UI — 7-tab layout (MAC/NECGC/NECTECH × Received/Spent + MAC-EZIDEBIT), import files, filter/search, bulk edit, per-instance upload, agent commission calculator |
| `tracker/api.py` | Optional FastAPI backend for the redesigned React frontend in `tracker/web/`. Reuses `database.py`, `parsers.py`, and `bulk_payment.py` |
| `tracker/web/` | React/JSX prototype (Babel-in-browser, no build step) — Linear/Stripe-style redesign with hero cards, drawers, and keyboard shortcuts. Served by `api.py` at `/` |
| `tracker/database.py` | SQLite database layer — `transactions` and `agent_profiles` tables, upsert, bulk update, stats |
| `tracker/parsers.py` | File parsers — bank CSV (single + combined multi-bank), Xero Excel, and Ezidebit PDF. Instance-aware account mapping. Dedup collision resolution for same-payer/same-amount transactions |
| `tracker/reconciler.py` | Reconciliation engine — classifies payment method and extracts student from transaction data |
| `tracker/agent_calculator.py` | Agent commission calculator — verifies agent deduction payments against expected amounts |
| `tracker/requirements.txt` | Dependencies: `streamlit`, `pandas`, `openpyxl`, `pdfplumber`, `fastapi`, `uvicorn[standard]`, `python-multipart` |
| `tracker/tracker.db` | SQLite database (gitignored — contains real transaction data) |

### Multi-Instance Architecture

Each transaction is tagged with an `instance` code based on its bank account:

| Bank Account | Instance Code | UI Tab Label |
|--------------|---------------|--------------|
| Adelaide, Brisbane Cheque, Brisbane Prepaid, Adelaide Prepaid | MAC | MAC |
| GC Cheque, GC Prepaid | NECGC | NECGC |
| Melbourne Cheque, Melbourne Prepaid | NEC | NECTECH |
| EZIDEBIT (from Ezidebit PDF reports) | EZIDEBIT | MAC-EZIDEBIT |

**Account mapping for bank CSV files** (`BANK_ACCOUNT_INSTANCE` in `parsers.py`):
- Account names are derived from CSV filenames (e.g., `GC Cheque.csv` → `GC Cheque`)
- Unmapped accounts default to `MAC`

**Account mapping for Xero Excel files** (`XERO_ACCOUNT_MAP` in `parsers.py`):
- Row 4, Column A in the "Bank Statement" tab contains the account identifier
- Exact-match lookup against the mapping dict; falls back to `split(" - ")[0]` for MAC accounts

**Ezidebit PDF files** (`parse_ezidebit_pdf()` in `parsers.py`):
- Parsed via `pdfplumber` text extraction with line-based regex matching (not table extraction — Ezidebit PDF column layouts vary per report and break table detection)
- The regex anchors on the stable line structure: two DD/MM/YYYY dates (trans + settlement), payer ID (`NNN-NNN-NNN`), payer name, client ref, `Paid`, and three dollar amounts
- Only "Paid" rows **with a settlement date** are imported (failed/declined and pending rows without a settlement date are naturally excluded because the regex requires both dates)
- Student ID is extracted from Client Contract Ref via regex (MAC ID like `MAC6007` or numeric ID like `12642082`) — raw name text is stripped
- Instance is always `EZIDEBIT`; uploads use MAC API credentials
- Location (campus) is extracted from PDF header text (e.g., "Macallan College - Brisbane" → "Brisbane")
- Transactions import directly as "OK to Upload" status
- The `location` column on the `transactions` table stores the campus code (BNE, SYD, PER, ADL) for future data segregation

### How It Works

1. **Import** — Upload bank CSV, Xero Excel, or Ezidebit PDF files via the Streamlit UI. The parsers auto-detect format and instance, run reconciliation to populate student and payment method, and upsert into SQLite (deduplication by date+amount+normalized payer+account). Ezidebit PDFs are parsed via line-based regex for "Paid" transactions that have a settlement date (pending/failed rows are excluded), with student ID extracted from Client Contract Ref (MAC ID or numeric ID) and status set directly to "OK to Upload". When multiple transactions share the same dedup key (e.g. an agent paying the same amount for two different students on the same day), the parsers append sequence numbers (`|2`, `|3`, …) in file order to ensure all transactions are preserved.
2. **Review** — Each instance has Received and Spent tabs. Filter by status, payment method, bank account, and student. Search across payer names, references, and descriptions. Select rows and bulk-edit student, status, or payment method.
3. **Mark for Upload** — Set transaction status to "OK to Upload" for rows ready to push to Axcelerate.
4. **Upload** — Use the per-instance upload buttons in the "Upload to Axcelerate" expander, which runs `bulk_payment.py --instance <CODE>` to read "OK to Upload" rows for that instance and record them via the correct Axcelerate API credentials.

### Transaction Statuses

| Status | Meaning |
|--------|---------|
| `Unreconciled` | New import, not yet reviewed |
| `OK to Upload` | Reviewed and ready for Axcelerate upload |
| `Axcelerate Updated` | Successfully recorded in Axcelerate (allocated to invoice) |
| `Unallocated` | Recorded in Axcelerate but no matching invoice found |
| `Check Manually` | Failed or needs manual intervention |
| `No Action` | Auto-set for Direct Debit, Stripe, Internal Transfer (handled elsewhere) |

### Agent Commission Calculator

The tracker includes a built-in calculator for verifying agent deduction payments. Education agents pre-deduct their commissions from payments they transfer, and this tool checks if the amount received is correct.

**How commission works:**
- Commission is charged **only on tuition fees** (admin fees and material fees are not commission-eligible)
- GST of 10% is applied on top of the commission
- Top-tier agents may also pre-deduct an **admin fee waiver** and/or a **bonus**
- Formula: `Expected Payment = Invoice Total - (Commission + GST + AF Waiver + Bonus)`

**Agent Profiles** (`agent_profiles` table in SQLite):
- Stores each agent's commission rate (30%, 35%, or 40%), admin fee waiver eligibility, bonus eligibility, and default bonus amount
- Profiles persist across sessions — select an agent and their terms auto-fill in the calculator

**Auto-fill from transaction table:**
- Select a single Agent Deduction row in any transaction tab → click the "📐 Calculator" button
- The payment amount is pre-filled and the payer name is matched against saved agent profiles
- The calculator section auto-expands with the transaction context displayed

### Running the Tracker

```bash
cd tracker
pip install -r requirements.txt
streamlit run app.py
```

### Optional FastAPI + React redesign

The redesigned UI in `tracker/web/` is a single-page React app loaded via Babel-in-browser (no build step). It talks to `tracker/api.py` (FastAPI), which wraps the same `database.py`, `parsers.py`, and `bulk_payment.py` the Streamlit app already uses — no schema duplication, no parallel SQLite, no copy of the API tokens. The Streamlit `tracker/app.py` is untouched and can run alongside on its own port.

```bash
cd tracker
pip install -r requirements.txt          # adds fastapi, uvicorn, python-multipart
python -m uvicorn api:app --port 8765    # serves the React frontend at http://127.0.0.1:8765
```

#### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`    | `/api/meta` | Returns statuses, payment methods, and instance metadata for the frontend |
| `GET`    | `/api/transactions` | All rows from `tracker.db` |
| `PATCH`  | `/api/transactions/{id}` | Update `status`, `payment_method`, or `student` (whitelisted fields only) |
| `POST`   | `/api/transactions/bulk` | Bulk PATCH for multi-select actions in the UI |
| `POST`   | `/api/transactions/{id}/prepare-upload` | Set `upload_amount` + `upload_description` and flip status to "OK to Upload" (used by the calculator's "Prepare for upload" button) |
| `POST`   | `/api/import` | Multi-file upload — runs each file through `parsers.detect_and_parse` + `database.upsert_transactions` |
| `POST`   | `/api/upload/{instance}` | Spawns `python bulk_payment.py --instance <code>` as a subprocess and returns stdout/stderr |

Status and `payment_method` values are validated against the lists in `tracker/api.py`. The `/api/upload/{instance}` endpoint shells out to `bulk_payment.py` — the same `.env` credentials and Axcelerate calls used by the Streamlit app.

#### Editing UX in the React frontend

- **Inline cell editing**: click any status pill, payment-method tag, or student name in the table to edit that single row. Status and method open a floating dropdown anchored to the cell (rendered via React portal so the row's `overflow: hidden` doesn't clip it); student opens an inline text input (Enter saves, Esc cancels, blur saves). Each edit fires `PATCH /api/transactions/{id}` optimistically and rolls back the local row on failure.
- **Bulk editing**: select rows with the row checkbox or `X` key, then use the floating action bar (`U` = OK to Upload, `R` = Axcelerate Updated, "Set status ▾" for any of the 6 statuses, "Set method ▾" for any of the 5 methods). Bulk operations POST to `/api/transactions/bulk`.
- **Shared DB, no auto-refresh**: both UIs read/write the same `tracker.db`. Changes are durable in either direction, but neither polls — click "Refresh" in the React top-bar (or reload the page) to pick up edits made in Streamlit since the React tab was loaded. Last-write-wins on concurrent edits to the same row.

## Bulk Payment Uploader

`bulk_payment.py` reads transactions with status "OK to Upload" from the tracker SQLite database and records each as a payment in the correct Axcelerate instance.

### Multi-Instance Support

The script accepts an `--instance` argument to select which Axcelerate instance to upload to:

```bash
python bulk_payment.py                      # Default: MAC
python bulk_payment.py --instance MAC       # Macallan College
python bulk_payment.py --instance NECGC     # NEC Gold Coast
python bulk_payment.py --instance NEC       # NEC Melbourne (NECTECH)
python bulk_payment.py --instance EZIDEBIT  # Ezidebit direct debits (uses MAC credentials)
```

Each instance uses its own API credentials from `.env` (see Instance Credential Mapping above). The SQL query filters by `instance` column to only process transactions for the selected instance.

The tracker app's "Upload to Axcelerate" section has per-instance buttons that call this script with the appropriate `--instance` argument.

### What It Does

1. Loads "OK to Upload" rows for the selected instance from `tracker/tracker.db`
2. Resolves contact IDs (numeric IDs used directly; MAC IDs looked up via optionalID search)
3. Searches for a matching invoice (balance == payment amount) across SENT, PARTIAL, and OVERDUE statuses
4. Records the payment — allocated to invoice if found, otherwise as unallocated credit
5. Updates tracker row status: `Axcelerate Updated` (allocated), `Unallocated` (no invoice match), or `Check Manually` (error)
6. Prints a session transaction report and saves a CSV report to `payment_report_<INSTANCE>_YYYYMMDD_HHMMSS.csv`

### Field Mapping (Tracker → Axcelerate)

| Tracker Column | Axcelerate Field |
|----------------|------------------|
| `student` | `contactID` (numeric ID or MAC optionalID) |
| `date` | `transDate` (converted from YYYY-MM-DD to MM/DD/YYYY) |
| `amount` | `amount` |
| `payment_method` | `paymentMethodID` (mapped via METHOD_MAP) |
| `bank_account` | `reference` and `description` |

## Reconciliation Engine

`tracker/reconciler.py` implements the classification rules from `axcelerate-reconcile.md`:

- **Payment Method Classification**: Direct Deposit, Agent Deduction, Direct Debit, Stripe, Internal Transfer
- **Student Extraction**: Student ID (8-digit) → MAC ID → Student Name → Unknown
- **Known Agent Detection**: 25+ agents with column-specific extraction preferences (PAYMENT FROM and TRANSFER FROM patterns)
- **Own Entity Detection**: `OWN_ENTITIES` list includes entity names for MAC and NECGC colleges — transactions from these entities are not misclassified as Agent Deductions

The reconciler is called automatically by the parsers during import. It can also be invoked directly:

```python
from reconciler import reconcile_transaction

result = reconcile_transaction(
    description="PAYMENT FROM ONEPOINT",
    payer="ONEPOINT",
    payee="MACALLAN EDUCATION",
    col_h="John Smith 01-01-2000",
    col_i="",
    amount=1500.00,
)
# result = {"student": "John Smith 01-01-2000", "payment_method": "Agent Deduction"}
```

## When Adding or Modifying Commands

- Each command file opens with `You are an expert at...` and accepts `$ARGUMENTS` for dynamic user input
- Include 3–6 complete, copy-paste-ready workflow patterns with realistic placeholder values
- Reference `.claude/axcelerate_api_reference.md` for accurate endpoint paths and required vs. optional fields
- Use `<PLACEHOLDER>` (not empty strings or `None`) for values the user must provide
