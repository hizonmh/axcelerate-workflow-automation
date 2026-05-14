# Axcelerate Workflow Automation

A Claude AI command library, MCP server, and automation toolkit for managing workflows against the [Axcelerate](https://www.axcelerate.com/) training management system REST API. Supports three Axcelerate instances (MAC, NECGC, NECTECH) across multiple colleges.

## What's In This Repo

| Component | Path | Purpose |
|---|---|---|
| Claude Code skills | [.claude/commands/](.claude/commands/) | Nine `/axcelerate-*` slash commands, one per API domain (contact, course, enrol, invoice, payment, email, report, reconcile, workflow) |
| MCP server | [axcelerate-mcp-server/](axcelerate-mcp-server/) | FastMCP server exposing 30+ Axcelerate operations as tools for any MCP-compatible client |
| Bank Transaction Tracker | [tracker/](tracker/) | Streamlit web app for importing, reconciling, and bulk-editing bank transactions before upload |
| Bulk Payment Uploader | [bulk_payment.py](bulk_payment.py) | Reads "OK to Upload" rows from the tracker and records them via the correct Axcelerate instance |
| Reconciliation Engine | [tracker/reconciler.py](tracker/reconciler.py) | Auto-classifies bank transactions by student and payment method |
| API reference | [.claude/axcelerate_api_reference.md](.claude/axcelerate_api_reference.md) | Full Axcelerate REST API reference (consulted by all commands) |

## Setup

### 1. Clone and install dependencies

```bash
git clone <this-repo>
cd "Axcelerate Workflow Automation"

# MCP server
pip install -r axcelerate-mcp-server/requirements.txt

# Tracker app
pip install -r tracker/requirements.txt
```

### 2. Configure credentials

Create a `.env` file in the repo root with API tokens for each instance you use. Tokens are issued from the Axcelerate admin panel.

```ini
# MAC instance (Macallan College)
AXCELERATE_API_TOKEN=...
AXCELERATE_WS_TOKEN=...
AXCELERATE_BASE_URL=...

# NECGC instance (NEC Gold Coast)
NECGC_API_TOKEN=...
NECGC_WS_TOKEN=...
NECGC_BASE_URL=...

# NECTECH instance (NEC Melbourne) - env prefix is NEC_
NEC_API_TOKEN=...
NEC_WS_TOKEN=...
NEC_BASE_URL=...
```

`.env` is gitignored. Never commit tokens.

### 3. Register the MCP server (optional)

The server is auto-registered for Claude Code via [.mcp.json](.mcp.json). For other MCP clients:

```bash
claude mcp add axcelerate -- python axcelerate-mcp-server/server.py
```

## Usage

### Claude Code slash commands

From any Claude Code session in this repo, invoke a command directly:

```
/axcelerate-contact search for John Smith
/axcelerate-enrol enrol contact 12345 in instance 67890
/axcelerate-workflow create contact, enrol, invoice, and email
```

The `/axcelerate-workflow` command is a master orchestrator that chains multiple domains together.

### Bank Transaction Tracker

```bash
cd tracker
streamlit run app.py
```

Workflow:
1. **Import** — upload bank CSVs, Xero Excel exports, or Ezidebit PDF reports. Parsers auto-detect the source and tag each row with its instance (MAC / NECGC / NEC / EZIDEBIT). Ezidebit imports only include "Paid" rows that have a settlement date (pending/failed rows are excluded).
2. **Review** — filter, search, and bulk-edit student/status/payment method across seven tabs (Received + Spent for each instance, plus MAC-EZIDEBIT for direct debits).
3. **Mark for upload** — set status to `OK to Upload` for verified rows.
4. **Upload** — use the per-instance buttons in the "Upload to Axcelerate" expander, which run `bulk_payment.py` with the correct `--instance` flag.

The tracker also includes an **agent commission calculator** for verifying agent deduction payments (pre-fills from a selected transaction row, supports per-agent profiles with commission rate, GST, admin fee waiver, and bonus).

### Bulk Payment Uploader (CLI)

```bash
python bulk_payment.py --instance MAC       # Macallan College
python bulk_payment.py --instance NECGC     # NEC Gold Coast
python bulk_payment.py --instance NEC       # NEC Melbourne
python bulk_payment.py --instance EZIDEBIT  # Ezidebit direct debits (uses MAC credentials)
```

For each "OK to Upload" row in `tracker/tracker.db` for the selected instance, the script:
1. Resolves the contact (numeric ID, or MAC ID via `optionalID` lookup)
2. Searches for a matching invoice (balance == amount, statuses SENT/PARTIAL/OVERDUE)
3. Records the payment — allocated to the invoice if found, otherwise as unallocated credit
4. Updates the tracker row to `Axcelerate Updated`, `Unallocated`, or `Check Manually`
5. Writes a CSV report to `payment_report_<INSTANCE>_YYYYMMDD_HHMMSS.csv`

## Instance Credential Mapping

| Instance | Display | API Token | WS Token | Base URL |
|---|---|---|---|---|
| MAC | MAC | `AXCELERATE_API_TOKEN` | `AXCELERATE_WS_TOKEN` | `AXCELERATE_BASE_URL` |
| NECGC | NECGC | `NECGC_API_TOKEN` | `NECGC_WS_TOKEN` | `NECGC_BASE_URL` |
| NEC | NECTECH | `NEC_API_TOKEN` | `NEC_WS_TOKEN` | `NEC_BASE_URL` |

## API Conventions (gotchas)

- **POST/PUT bodies must be form-encoded** (`data=`), not JSON. Using `json=` silently fails or returns wrong defaults.
- **Date format is `DD/MM/YYYY`** for most endpoints, but `transDate` on payment transactions uses `MM/DD/YYYY`. Verify in the API reference.
- **IDs are numeric** except invoice GUIDs, which are string UUIDs.
- **Error responses** include `error`, `code`, `messages`, and `details` — always call `raise_for_status()`.

See [.claude/CLAUDE.md](.claude/CLAUDE.md) for full developer guidance.

## Repo Hygiene

The following are gitignored and must not be committed:
- `.env` — API tokens
- `tracker/tracker.db` — real transaction data
- `payments/`, `legacy payments/`, `bank files/` — operational data with real student/payment records
- `payment_report_*.csv` — generated upload reports
- `SOP - Recording Payments in Axcelerate.md` — internal procedures

## License

Internal tooling. Not licensed for external distribution.
