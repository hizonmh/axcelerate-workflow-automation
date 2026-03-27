# Axcelerate Bank CSV Reconciliation

You are an expert at reconciling raw bank transaction files from Macallan College, NECGC, and NECTECH bank accounts. You process and reconcile bank CSVs by adding two columns: **Student** (who the payment is for) and **Payment Method** (how it was paid). The system supports three Axcelerate instances: MAC, NECGC, and NEC (NECTECH).

## Trigger Prompts

Upload your bank CSV file and say any of these:
- "Reconcile these bank payments"
- "Process this bank transaction file"
- "New bank file — please process and reconcile"

$ARGUMENTS

## Input File Structure

| Column | Name | Description |
|--------|------|-------------|
| A | Source.Name | Bank account name (e.g., Adelaide.csv, Brisbane Cheque.csv) |
| B | Column1 | Transaction date (serial number). Non-date data = extra info for previous row |
| C | Column2 | Transaction amount. **ONLY process positive values** (incoming). Negative = outgoing, skip |
| D | Column3 | Primary transaction description |
| E | Column4 | Secondary description (usually payer name) |
| F | Column5 | Tertiary description (usually Macallan entity name) |
| G | Column6 | Usually empty |
| H | Column7 | Additional reference (often student ID or name) |
| I | Column8 | Additional reference (often fee description or student info) |

## Output Columns

### Column J: "Student"

Extract student identifier using this priority order:

| Priority | Type | Description |
|----------|------|-------------|
| 1 | Student ID | 8-digit number starting with 1 (e.g., 12826971). Search ALL columns D–I. |
| 2 | MAC ID | Format: MAC + 4 digits (e.g., MAC6174). Normalize spaces: "MAC 6174" → "MAC6174" |
| 3 | Student Name | If no ID found, extract the student's name from context |
| 4 | Name + Extra Info | If student included DOB or other info (e.g., M. Hassan Raza Khan 20-03-1997), keep it |
| 5 | "Unknown" | No student info determinable (Ezidebit batches, internal transfers) |

### Column K: "Payment Method"

| Method | How to Identify |
|--------|----------------|
| Direct Deposit | Most common. Single person name, no organization. Rounded amounts. Includes ATM deposits labeled "AGENT DEPOSIT" + student ID. Includes family/friends paying for student. |
| Agent Deduction | Organization name in payer (PTY, LTD, INTERNATIONAL, GROUP, GLOBAL). OR two different names (payer ≠ student). OR TRANSFER FROM [agent] patterns. |
| Direct Debit | Contains EZIDEBIT in description. |
| Stripe | Contains STRIPE in description. |
| Internal Transfer | Contains FUNDS TFER + FROM in description. Transfers between Macallan's own bank accounts. |

## Critical Rules

- **"AGENT DEPOSIT"** = ATM cash deposit by student = **Direct Deposit** (NOT Agent Deduction). Student ID follows immediately after.
- **#NAME?** in col E: CSV import converts names starting with "-" to #NAME? errors. Extract actual name from col D instead.
- **7-digit IDs are NOT valid** student IDs. Only 8-digit numbers starting with 1 are valid. Use student name instead.
- **Embedded IDs**: Student IDs can be embedded without spaces (e.g., 12829372kibet). Use regex `(1\d{7})` to extract.
- For **Agent Deductions**, Column J shows the **STUDENT** (person being paid for), NOT the payer/agent.
- Individual persons paying for a **DIFFERENT** student are Agent Deductions (not Direct Deposit) if they are repeat/known agents. Only classify as Direct Deposit if payer is clearly family/friend with no agent history. When in doubt and payer ≠ student, default to Agent Deduction.
- If col E is a person BUT col F is **NOT** a Macallan entity (e.g., Clear Eyed Pty Ltd) → Agent Deduction.
- Ezidebit batch transfers and internal transfers: student = "Unknown", needs manual reconciliation.

## Known Agents & Organizations

### PAYMENT FROM Agents

| Agent Name | Where to Find Student |
|------------|----------------------|
| OnePoint | Col H: student name + DOB |
| Edunetwork PTY LTD | Col I: format NP[amount] - [ref] - [Student Name] |
| Spot On Global | Col H: student name, Col I: Student ID |
| EHUB International PTY LTD | Col I: student info |
| E-COLINK | Col H: student name |
| DRM | Col H: student name |
| MigrationArcadia | Col H: student name (remove "Fee Transfer Receipt") |
| Qualy Pay | Col I: student name (remove "QLY " prefix) |
| Spark Group International | Col H: student name |
| Primo Group Australia | Col H: student name |
| Top Notch Study and Visa | Col I: remove leading numbers and "Macallan fee" |
| New Era International PTY LTD | Col I: student name |
| Student Vibes PTY LTD | Col H: student info, ID extractable |
| Clear Eyed PTY LTD | Appears in Col F (not Macallan). Student in Col I |
| Vanesa Correa Mejia | Agent with INV reference. Student name in Col H |
| Ankita Chopra | Agent with inv reference. Student ID in Col I |
| Ankit Arora | Pays for different students. Student info in Col I |
| Angela Sthefania Carrasco | Individual agent. Student name in Col I, student ID may need manual lookup. |
| Justice Fami | Individual agent. Student info in Col H (format: Name-StudentID e.g. Hassan-11439444). Extract student ID after hyphen. |
| Kiran | Individual agent. Col E may show #NAME? (dash prefix). Student name in Col I (clean fee text e.g. "Nikhil_Fee" → "Nikhil"). |

### TRANSFER FROM Agents

| Agent Name | Where to Find Student |
|------------|----------------------|
| Aussizz Migration | Extract ID from ID:[8digits] in col D |
| Shabbir Iqbal | Student name follows after multiple spaces in col D |
| CBA | Student ID embedded in col D |
| G8M8 Great Mate | Student name between agent name and "MACALL" in col D |

## Processing Workflow

### Step 1: Read Data

Read all rows from the uploaded file/sheet. Identify column structure (should match input format above).

### Step 2: Process Each Row

For each row with positive amount (Col C > 0):
1. Combine all description fields (D–I) into searchable text
2. Determine Payment Method using classification rules
3. Extract Student Identifier (ID → MAC ID → Name → Name+Info → Unknown)
4. For negative amounts, leave columns J and K blank

### Step 3: Write Results

Add headers "Student" (J1) and "Payment Method" (K1) bold. Write all results. Format Col J as text. Auto-fit widths.

### Step 4: Verify & Summarize

Spot-check sample rows across different payment methods and provide a summary report:
- Total rows, positive (incoming) count, negative/skipped count
- Breakdown by Payment Method (Direct Deposit, Agent Deduction, Direct Debit, Stripe, Internal Transfer)
- Breakdown by Student ID type (Student ID, MAC ID, Name, Name+Info, Unknown)
- Flag "Unknown" rows that need manual review

## Student Name Extraction (for Agent Deductions)

1. Check Col I first — often contains student name or "student name + ID"
2. Check Col H — sometimes has student info
3. Clean names by removing fee text: college fees, school fee, tuition, payment, deposit, COE, enrolment, certificate, cert III, advance diploma, installment, etc.
4. Remove MR, MRS, MS prefixes from names
5. For TRANSFER FROM patterns: student info appears after multiple spaces following the agent name
6. For Edunetwork: parse format `NP[amount] - [ref] - [Student Name]` from Col I

## Implementation

Reconciliation is implemented in the **Bank Transaction Tracker** app (`tracker/` directory):

### Key Files

| File | Purpose |
|------|---------|
| `tracker/reconciler.py` | Core reconciliation engine — `reconcile_transaction()`, `classify_payment_method()`, `extract_student()` |
| `tracker/parsers.py` | File parsers — bank CSV (single + combined multi-bank), Xero Excel, and Ezidebit PDF. Calls reconciler automatically on import |
| `tracker/database.py` | SQLite database — stores transactions with deduplication, status tracking, bulk updates |
| `tracker/app.py` | Streamlit web UI — import files, review/edit reconciled transactions, mark for upload |
| `bulk_payment.py` | Upstream: reads "OK to Upload" rows from tracker DB and records payments in Axcelerate |

### Reconciliation Engine (`tracker/reconciler.py`)

The reconciler classifies each incoming transaction by:

1. **Payment Method** (`classify_payment_method()`):
   - Checks for Stripe, Ezidebit (Direct Debit), FUNDS TFER (Internal Transfer)
   - Checks known PAYMENT FROM / TRANSFER FROM agents → Agent Deduction
   - Checks org keywords in payer name (PTY, LTD, etc.) → Agent Deduction
   - Checks Col F payee against `OWN_ENTITIES` list (non-own entity) → Agent Deduction
   - Checks payer ≠ student (different names in payer vs references) → Agent Deduction
   - Default → Direct Deposit

2. **Student** (`extract_student()`):
   - Priority 1: 8-digit Student ID (`1\d{7}`) from all columns
   - Priority 2: MAC ID (`MAC\s?\d{4}`)
   - Agent Deduction: agent-specific column preference (h/i/hi/d) from `PAYMENT_FROM_AGENTS` dict
   - Direct Deposit: payer name (cleaned of fee/noise words)
   - Internal Transfer / Direct Debit: "Unknown"

### Multi-Instance Support

Transactions are automatically tagged with an `instance` code based on bank account:

| Bank Account | Instance | UI Label |
|--------------|----------|----------|
| Adelaide, Brisbane Cheque/Prepaid, Adelaide Prepaid | MAC | MAC |
| GC Cheque, GC Prepaid | NECGC | NECGC |
| Melbourne Cheque, Melbourne Prepaid | NEC | NECTECH |
| EZIDEBIT (from Ezidebit PDF reports) | EZIDEBIT | MAC-EZIDEBIT |

Account-to-instance mapping is defined in `parsers.py` via `BANK_ACCOUNT_INSTANCE` (for CSV) and `XERO_ACCOUNT_MAP` (for Xero Excel).

### Data Flow

```
Bank CSV / Xero Excel / Ezidebit PDF
    ↓ parsers.py (detect_and_parse, auto-detect instance from account)
    ↓ reconciler.py (auto-classify student + method; Ezidebit pre-populated)
    ↓ database.py (upsert with dedup, instance + location columns)
    ↓ app.py (7-tab Streamlit UI: MAC/NECGC/NECTECH × Received/Spent + MAC-EZIDEBIT)
    ↓ bulk_payment.py --instance <CODE> (upload to correct Axcelerate instance)
```

### Supported File Formats

| Format | Parser | Description |
|--------|--------|-------------|
| Combined bank CSV | `parse_combined_bank_csv()` | Multi-bank merged file with Source.Name header |
| Single bank CSV | `parse_bank_csv()` | Per-bank CSV (8 columns, no header, DD/MM/YYYY dates) |
| Xero Excel | `parse_xero_excel()` | Bank Reconciliation export (.xlsx), reads "Bank Statement" tab |
| Ezidebit PDF | `parse_ezidebit_pdf()` | Processed Payments Report PDF. Only "Paid" rows with a settlement date are imported (pending rows without settlement date are skipped). Status set to "OK to Upload". Location extracted from header (e.g. "Macallan College - Brisbane") |

### Transaction Statuses (Tracker)

| Status | Meaning |
|--------|---------|
| `Unreconciled` | Newly imported, not yet reviewed |
| `OK to Upload` | Reviewed and ready for Axcelerate upload |
| `Axcelerate Updated` | Successfully recorded in Axcelerate |
| `Unallocated` | Recorded but no matching invoice found |
| `Check Manually` | Error or needs manual review |
| `No Action` | Auto-set for Direct Debit, Stripe, Internal Transfer |

## Updating This Skill

When new patterns are discovered during reconciliation:
- **New PAYMENT FROM agents**: Add to `PAYMENT_FROM_AGENTS` dict in `tracker/reconciler.py` with column preference (h/i/hi/d)
- **New TRANSFER FROM agents**: Add to `TRANSFER_FROM_AGENTS` list in `tracker/reconciler.py`
- **New organisation keywords**: Add to `ORG_KEYWORDS` list
- **New own entity names**: Add to `OWN_ENTITIES` list (prevents false agent detection for MAC, NECGC, NECTECH entities)
- **New fee/noise words**: Add to `FEE_WORDS` set (cleaned from student name extraction)
- Update this file with the new patterns for future reference
