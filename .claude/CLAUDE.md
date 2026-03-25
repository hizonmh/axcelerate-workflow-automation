# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **Claude AI command library, MCP server, and automation toolkit** for managing workflows against the **Axcelerate training management system** REST API. It contains:

- **Claude Code skills** (prompt commands) for each API domain
- A **Model Context Protocol (MCP) server** exposing Axcelerate API as tools for any MCP-compatible client
- A **Bank Transaction Tracker** (Streamlit web app) for importing, reconciling, and managing bank transactions
- A **Bulk Payment Uploader** script that reads reconciled transactions from the tracker and records them in Axcelerate
- A **Reconciliation Engine** that auto-classifies bank transactions by student and payment method

## Repository Structure

- `.claude/axcelerate_api_reference.md` — Full API reference (68KB). Always consult this first when looking up endpoint paths, parameters, and response shapes.
- `.claude/commands/*.md` — Nine modular Claude commands, each scoped to one API domain. These are the skills invoked via `/axcelerate-*` commands.
- `.claude/settings.local.json` — Restricts `WebFetch` to `app.axcelerate.com` and `developer.axcelerate.com` only.
- `axcelerate-mcp-server/` — MCP server exposing Axcelerate API as tools (see below).
- `tracker/` — Bank Transaction Tracker app (see below).
- `bulk_payment.py` — Bulk payment uploader script (see below).
- `.mcp.json` — Project-level MCP server registration for Claude Code.
- `.env` — API tokens (gitignored, never committed)
- `payments/` — Operational payment data and legacy scripts (gitignored, never committed)

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

All generated Python code loads credentials from a `.env` file using `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
API_TOKEN = os.getenv("AXCELERATE_API_TOKEN")
WS_TOKEN  = os.getenv("AXCELERATE_WS_TOKEN")
BASE_URL  = os.getenv("AXCELERATE_BASE_URL")  # e.g. https://{subdomain}.app.axcelerate.com/api

headers = {
    "apitoken": API_TOKEN,
    "wstoken": WS_TOKEN,
}
```

Both tokens come from the Axcelerate admin panel. The base URL is instance-specific (each organisation has its own subdomain). Use `<PLACEHOLDER>` in generated code for any value the user must supply. **Never hardcode tokens in scripts.**

## Key API Conventions

- **POST encoding**: All `POST` and `PUT` requests must use **form encoding** (`data=`), NOT JSON (`json=`). Using JSON will silently fail or return incorrect defaults.
- **Date format**: `DD/MM/YYYY` for most endpoints (some accept `YYYY-MM-DD` — verify in `.claude/axcelerate_api_reference.md`)
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
- Reads credentials from `.env` (`AXCELERATE_API_TOKEN`, `AXCELERATE_WS_TOKEN`, `AXCELERATE_BASE_URL`)

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

The `tracker/` directory contains a Streamlit web app for importing, reconciling, and managing bank transactions before uploading them to Axcelerate.

### Components

| File | Purpose |
|------|---------|
| `tracker/app.py` | Streamlit UI — import files, filter/search transactions, bulk edit status/student/method |
| `tracker/database.py` | SQLite database layer — `transactions` table with upsert, bulk update, stats |
| `tracker/parsers.py` | File parsers — bank CSV (single and combined multi-bank), Xero Excel reconciliation exports |
| `tracker/reconciler.py` | Reconciliation engine — classifies payment method and extracts student from transaction data |
| `tracker/requirements.txt` | Dependencies: `streamlit`, `pandas`, `openpyxl` |
| `tracker/tracker.db` | SQLite database (gitignored — contains real transaction data) |

### How It Works

1. **Import** — Upload bank CSV or Xero Excel files via the Streamlit UI. The parsers auto-detect format, run reconciliation to populate student and payment method, and upsert into SQLite (deduplication by date+amount+payer+account).
2. **Review** — Filter by status, payment method, bank account, and student. Search across payer names, references, and descriptions. Select rows and bulk-edit student, status, or payment method.
3. **Mark for Upload** — Set transaction status to "OK to Upload" for rows ready to push to Axcelerate.
4. **Upload** — Run `bulk_payment.py` to read "OK to Upload" rows from the tracker DB and record them in Axcelerate via the API.

### Transaction Statuses

| Status | Meaning |
|--------|---------|
| `Unreconciled` | New import, not yet reviewed |
| `OK to Upload` | Reviewed and ready for Axcelerate upload |
| `Axcelerate Updated` | Successfully recorded in Axcelerate (allocated to invoice) |
| `Unallocated` | Recorded in Axcelerate but no matching invoice found |
| `Check Manually` | Failed or needs manual intervention |
| `No Action` | Auto-set for Direct Debit, Stripe, Internal Transfer (handled elsewhere) |

### Running the Tracker

```bash
cd tracker
pip install -r requirements.txt
streamlit run app.py
```

## Bulk Payment Uploader

`bulk_payment.py` reads transactions with status "OK to Upload" from the tracker SQLite database and records each as a payment in Axcelerate.

### What It Does

1. Loads "OK to Upload" rows from `tracker/tracker.db`
2. Resolves contact IDs (numeric IDs used directly; MAC IDs looked up via optionalID search)
3. Searches for a matching invoice (balance == payment amount) across SENT, PARTIAL, and OVERDUE statuses
4. Records the payment — allocated to invoice if found, otherwise as unallocated credit
5. Updates tracker row status: `Axcelerate Updated` (allocated), `Unallocated` (no invoice match), or `Check Manually` (error)
6. Prints a session transaction report and saves a CSV report to `payment_report_YYYYMMDD_HHMMSS.csv`

### Field Mapping (Tracker → Axcelerate)

| Tracker Column | Axcelerate Field |
|----------------|------------------|
| `student` | `contactID` (numeric ID or MAC optionalID) |
| `date` | `transDate` (converted from YYYY-MM-DD to DD/MM/YYYY) |
| `amount` | `amount` |
| `payment_method` | `paymentMethodID` (mapped via METHOD_MAP) |
| `bank_account` | `reference` and `description` |

### Running

```bash
python bulk_payment.py
```

## Reconciliation Engine

`tracker/reconciler.py` implements the classification rules from `axcelerate-reconcile.md`:

- **Payment Method Classification**: Direct Deposit, Agent Deduction, Direct Debit, Stripe, Internal Transfer
- **Student Extraction**: Student ID (8-digit) → MAC ID → Student Name → Unknown
- **Known Agent Detection**: 25+ agents with column-specific extraction preferences (PAYMENT FROM and TRANSFER FROM patterns)

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
