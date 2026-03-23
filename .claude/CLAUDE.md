# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **Claude AI command library and MCP server** for automating workflows against the **Axcelerate training management system** REST API. It contains prompt instructions, Python code templates, and a Model Context Protocol (MCP) server that exposes Axcelerate API operations as tools for any MCP-compatible client (Claude Code, Claude Desktop).

## Repository Structure

- `.claude/axcelerate_api_reference.md` — Full API reference (68KB). Always consult this first when looking up endpoint paths, parameters, and response shapes.
- `.claude/commands/*.md` — Nine modular Claude commands, each scoped to one API domain. These are the skills invoked via `/axcelerate-*` commands.
- `.claude/settings.local.json` — Restricts `WebFetch` to `app.axcelerate.com` and `developer.axcelerate.com` only.
- `axcelerate-mcp-server/` — MCP server exposing Axcelerate API as tools (see below).
- `.mcp.json` — Project-level MCP server registration for Claude Code.
- `.env` — API tokens (gitignored, never committed)
- `payments/` — Operational payment data and scripts (gitignored, never committed)

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

## When Adding or Modifying Commands

- Each command file opens with `You are an expert at...` and accepts `$ARGUMENTS` for dynamic user input
- Include 3–6 complete, copy-paste-ready workflow patterns with realistic placeholder values
- Reference `.claude/axcelerate_api_reference.md` for accurate endpoint paths and required vs. optional fields
- Use `<PLACEHOLDER>` (not empty strings or `None`) for values the user must provide
