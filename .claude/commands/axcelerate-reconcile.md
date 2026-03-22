# Axcelerate Bank CSV Reconciliation

You are an expert at reconciling raw ANZ bank transaction CSVs for Macallan Education. This is a weekly workflow that transforms bank exports into a reconciled file identifying which student each payment belongs to and what payment method was used.

## Context

Macallan Education operates **7 ANZ bank accounts** across 4 campuses:
- Adelaide (Adelaide .csv)
- Brisbane Cheque, Brisbane Prepaid (Brisbane Cheque.csv, Brisbane Prepaid.csv)
- Perth Cheque, Perth Prepaid (Perth Cheque.csv, Perth Prepaid.csv)
- Sydney Cheque, Sydney Prepaid (Sydney Cheque.csv, Sydney Prepaid.csv)

Raw bank exports are combined into a single CSV file (typically `payments/CSV_Macallan.csv`) which is then processed by `payments/reconcile_bank_csv.py`.

## How to Run

$ARGUMENTS

When the user asks to reconcile bank transactions:

1. **Check if a new CSV file was provided.** The input file should be placed at `payments/CSV_Macallan.csv`. If the user specifies a different filename, update the `INPUT_CSV` path in `reconcile_bank_csv.py`.

2. **Run the script:**
   ```
   python payments/reconcile_bank_csv.py
   ```

3. **Review the output** at `payments/CSV_Macallan_reconciled.csv`. Spot-check key rows and flag any "unknown" students for the user to manually identify.

4. **If the user wants to proceed to bulk payment recording**, the reconciled CSV needs to be transformed into the `Macallan_payments.csv` format: `contact_id, date, amount, payment_method, reference`. This is a separate step done after manual review.

## Input CSV Format

| Column | Name | Description |
|--------|------|-------------|
| 0 | Source.Name | Bank account name (e.g., "Adelaide .csv") |
| 1 | Column1 | Transaction date (DD/MM/YYYY or Excel serial number). **If not a date, it's continuation text for the previous row's Column8** |
| 2 | Column2 | Transaction amount. Positive = incoming, Negative = outgoing |
| 3 | Column3 | Transaction description (e.g., "PAYMENT FROM JOHN SMITH 12345678") |
| 4 | Column4 | Payer name. May show `#NAME?` (Excel error from leading dash) or `-` |
| 5 | Column5 | Payee name (usually a Macallan entity) |
| 6 | Column6 | (Often empty) |
| 7 | Column7 | Reference field 1 (often contains student ID or MAC code) |
| 8 | Column8 | Reference field 2 (free-text reference from payer) |

### Excel Serial Date Handling
Some rows have Excel serial date numbers (e.g., `46078`) instead of `DD/MM/YYYY` dates. This happens when Excel auto-converts dates during export. The script detects 5-digit numbers in the 40000–55000 range and converts them to `DD/MM/YYYY` using Excel's epoch (Dec 30, 1899).

### Multi-line Row Handling
Some transactions span multiple CSV rows. When Column1 contains text instead of a date (e.g., "Full name:- Rajesh Kumar Sharma"), it is extra information belonging to the **previous** row's Column8. The script concatenates these automatically.

## Output Columns Added

| Column | Name | Description |
|--------|------|-------------|
| 9 | Student | Student ID, MAC optional ID, student name, or "unknown" |
| 10 | Payment Method | Stripe, Direct Debit, Agent Deduction, or Direct Deposit |

## Student Identification Rules (Column 9)

Priority order for identifying the student:

### 1. Student ID (8-digit number)
- Format: 8 digits, typically starting with 11, 12, or 13 (e.g., `12000001`)
- Search columns 7, 6, 3, 4, 8 in that priority order
- Can be embedded in text like `SID13000001`, `ID:13000002KUMAR`, `_12000003`, `STDID.13000004PATEL`
- When multiple IDs found in one column, take the **last match** (student IDs tend to appear after "REF:" keywords, while passport numbers etc. appear earlier)
- Regex: `(?<!\d)(1[0-9]{7})(?!\d)` — ensures the 8-digit number isn't part of a longer number

### 2. Optional ID (MAC code)
- Format: `MAC` + 4 digits (e.g., `MAC0001`, `MAC0002`)
- Students sometimes write with a space: `Mac 0003` → normalised to `MAC0003`
- Regex: `\bMAC\s?(\d{4})\b` (case-insensitive)

### 3. Student Name
- **Direct Deposit**: Use the payer name from Column4 (the student IS the payer)
- **Agent Deduction**: Check if Column4 (payer) is the agent or the student:
  - If payer name contains agent keywords, "PTY LTD", or is a proxy payer (different person in references) → payer is the agent/proxy, look for student name in Column7/8 references
  - If payer name is a person and matches references → payer is the student
- **Proxy payments**: When Column4 payer name shares no significant words with Column7/8 reference names, the payer is paying for a different student. The student name comes from the reference, not the payer. Examples: RAVI KUMAR paying for "Priya Patel", AMIT VERMA paying for "Deepak Sharma"
- **Fallback**: Extract name from Column3 using `PAYMENT FROM (?:-\s*)?(.+?)` regex
- Filter out non-name values: "fees", "fee", "payment", "initial payment", "school", etc.

### 4. Unknown
- When no student ID, MAC code, or identifiable name is found
- These require manual review in the system

## Payment Method Classification Rules (Column 10)

### 1. Stripe
- Any column contains "STRIPE" (case-insensitive)

### 2. Direct Debit
- Any column contains "EZIDEBIT"
- These are automatic deductions via the Ezidebit payment gateway

### 3. Agent Deduction
Detected by any of these indicators:
- **Agent keywords** in any column: MIGRATION, AUSSIZZ, GLOBAL EDUCA, PREMIER EDUCATION, PACIFIC EDUCA, GATEWAY MIGRAT, HORIZON MIGRATION, VISA CONNECT, CROWN INTERNATIONAL, APEX MIGRATION, NOVA ASSIST
- **PTY LTD** in payer name (Column3 or Column4) — indicates a company/institution paying
- **TRANSFER FROM** pattern in Column3 (excluding EZIDEBIT transfers)
- **Proxy payment** — payer name (Column4) is a different person from the name in reference columns (Column7/8). Detected by comparing name words: if the payer and reference share no significant words (after filtering out noise like "fee", "payment", "school" etc.), the payer is paying on behalf of a different student. Requires at least 2 name-like words in the reference to trigger.
- Typically involves a migration agent, education consultant, or individual paying on behalf of a student
- Amounts are often non-round numbers (e.g., $615, $668, $1,230)

**Important**: "AGENT DEPOSIT" in Column3 is NOT an agent payment — it's how ANZ labels ATM cash deposits by students. These are classified as Direct Deposit.

### 4. Direct Deposit (default)
- Individual student paying directly via bank transfer
- Usually a single person's name in the transaction
- Amounts are typically round numbers (e.g., $1,000, $1,500, $2,000)

## Non-Student Positive Transactions

These are positive amounts that are NOT student fee payments. They are tagged in Column 9 with Column 10 = "N/A":

| Pattern in Column3 | Tag |
|---|---|
| `ANZ INTERNET BANKING FUNDS TFER` | INTERNAL TRANSFER |
| `REVERSAL OF DEBIT ENTRY` | REVERSAL |
| `INVALID CREDIT ACCOUNT` | BOUNCED |
| `VISA DEBIT DEPOSIT` | MERCHANT REFUND |

## Key Files

| File | Purpose |
|------|---------|
| `payments/reconcile_bank_csv.py` | The reconciliation script |
| `payments/CSV_Macallan.csv` | Input: raw bank export (replaced weekly) |
| `payments/CSV_Macallan_reconciled.csv` | Output: enriched with Student + Payment Method |
| `payments/Macallan_bulk.py` | Downstream: bulk payment recorder (uses reconciled data after manual review) |
| `payments/Macallan_payments.csv` | Downstream: formatted input for bulk recorder |

## Common Edge Cases

| Scenario | Example | How It's Handled |
|----------|---------|------------------|
| `#NAME?` in payer name | Excel error from leading `-` | Treated as invalid, name extracted from Column3 instead |
| Passport number vs Student ID | `PP NO: A16723660 ... REF: 12000001` | Column-priority search + last-match picks the correct REF |
| Agent paying for student | `APEX MIGRATION PTY LTD SARAH 13000001` | Agent detected, student ID extracted, classified as Agent Deduction |
| Student paying via agent reference | `MOHAMMED ALI Premier Education migration` | Payer is NOT an agent → student = MOHAMMED ALI |
| ID embedded without separator | `SID13000001`, `ID:13000002KUMAR` | Lookaround regex catches IDs not at word boundaries |
| Multi-line continuation | Row with "Full name:- Rajesh..." in date column | Appended to previous row's Column8 |
| "Macallan Education Consortium PTY" in Column5 | Payee is Macallan itself | Column5 is never checked for PTY LTD agent detection |
| ATM deposit labelled "AGENT DEPOSIT" | `AGENT DEPOSIT 12000003` | NOT an agent — ATM label. Classified as Direct Deposit |
| Person paying for different person | `RAVI KUMAR` paying, ref says `Priya Patel fee` | Proxy detection: no shared name words → Agent Deduction, student = reference name |
| Person paying for different person with ID | `PRIYA NAIR` paying, ref says `Vikram Singh` | Proxy detected, student ID from Col7 used, Agent Deduction |
| Proxy with DOB in reference | `AMIT VERMA` paying, ref `Deepak Sharma (01/01/2000)` | Proxy detected, student = "Deepak Sharma (01/01/2000)" |
| Reference has agent keyword (not proxy) | `MOHAMMED ALI`, ref `Premier Education migration` | Reference contains MIGRATION → skipped by proxy check → student = MOHAMMED ALI |

## Updating This Skill

When new patterns are discovered during reconciliation:
- **New agent names**: Add to `AGENT_KEYWORDS` list in `reconcile_bank_csv.py`
- **New non-name values**: Add to `NON_NAME_VALUES` set
- **New non-student transaction types**: Add to `NON_STUDENT_PATTERNS` list
- **New organisation entity names**: Note that Column5 payee names for the organisation's own entities are not agents — do not trigger agent detection on these
- **New noise words**: Add to `NAME_NOISE_WORDS` set in `reconcile_bank_csv.py` if payment descriptors cause false proxy detection
- Update this file with the new patterns for future reference
