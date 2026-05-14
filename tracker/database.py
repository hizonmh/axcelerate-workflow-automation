import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    if column not in _table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            payer_name TEXT,
            reference TEXT,
            payment_note TEXT,
            source TEXT,
            bank_account TEXT NOT NULL DEFAULT '',
            student TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Unreconciled',
            payment_method TEXT NOT NULL DEFAULT 'Direct Deposit',
            dedup_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Schema migrations — use PRAGMA table_info so we don't swallow real DB errors.
    _ensure_column(conn, "transactions", "bank_account", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "transactions", "student", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "transactions", "updated_at", "TEXT")
    _ensure_column(conn, "transactions", "instance", "TEXT NOT NULL DEFAULT 'MAC'")
    _ensure_column(conn, "transactions", "location", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "transactions", "upload_amount", "REAL")
    _ensure_column(conn, "transactions", "upload_description", "TEXT")
    # Idempotency: when bulk_payment.py successfully posts to Axcelerate it writes
    # the returned TRANSACTIONID/INVOICEID here BEFORE flipping status. Re-runs
    # then skip rows that already have a tx id, so a network blip after a
    # successful POST cannot cause a duplicate payment.
    _ensure_column(conn, "transactions", "axcelerate_transaction_id", "TEXT")
    _ensure_column(conn, "transactions", "axcelerate_invoice_id", "TEXT")

    # Agent profiles table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT UNIQUE NOT NULL,
            commission_rate REAL NOT NULL DEFAULT 0.30,
            admin_fee_waiver INTEGER NOT NULL DEFAULT 0,
            bonus_eligible INTEGER NOT NULL DEFAULT 0,
            default_bonus REAL NOT NULL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()


def upsert_transactions(records: list[dict]) -> dict:
    """Insert new transactions, updating Xero records if CSV has richer data.

    Returns dict with counts: inserted, updated, skipped.
    """
    conn = get_connection()
    cur = conn.cursor()
    inserted = updated = skipped = 0

    for rec in records:
        # Check if this dedup_key already exists
        existing = cur.execute(
            "SELECT id, source FROM transactions WHERE dedup_key = ?",
            (rec["dedup_key"],),
        ).fetchone()

        if existing is None:
            # New record — insert
            method = rec.get("payment_method", "Direct Deposit")
            # Allow parser to override status (e.g. Ezidebit sets "OK to Upload")
            if "status" in rec:
                status = rec["status"]
            else:
                no_action_methods = {"Direct Debit", "Stripe", "Internal Transfer"}
                status = "No Action" if method in no_action_methods else "Unreconciled"
            cur.execute(
                """INSERT INTO transactions
                   (date, amount, description, payer_name, reference, payment_note, source, bank_account, student, status, payment_method, dedup_key, created_at, instance, location)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rec["date"],
                    rec["amount"],
                    rec["description"],
                    rec["payer_name"],
                    rec["reference"],
                    rec["payment_note"],
                    rec["source"],
                    rec.get("bank_account", ""),
                    rec.get("student", ""),
                    status,
                    method,
                    rec["dedup_key"],
                    datetime.now().isoformat(),
                    rec.get("instance", "MAC"),
                    rec.get("location", ""),
                ),
            )
            inserted += 1
        elif rec["source"] == "Bank CSV" and existing["source"] == "Xero":
            # CSV is preferred — update the existing Xero record with richer CSV data.
            # Check if the row has already been actioned (anything beyond Unreconciled).
            # If so, only update informational fields — preserve student, payment_method, status.
            existing_row = cur.execute(
                "SELECT status FROM transactions WHERE id = ?",
                (existing["id"],),
            ).fetchone()
            already_actioned = existing_row["status"] not in ("Unreconciled", "No Action")

            if already_actioned:
                # Preserve reconciliation fields, only enrich descriptive data
                cur.execute(
                    """UPDATE transactions
                       SET description = ?, payer_name = ?, reference = ?, payment_note = ?,
                           source = ?, bank_account = ?, updated_at = ?
                       WHERE id = ?""",
                    (
                        rec["description"],
                        rec["payer_name"],
                        rec["reference"],
                        rec["payment_note"],
                        rec["source"],
                        rec.get("bank_account", ""),
                        datetime.now().isoformat(),
                        existing["id"],
                    ),
                )
            else:
                # Not yet actioned — full update including reconciliation fields
                cur.execute(
                    """UPDATE transactions
                       SET description = ?, payer_name = ?, reference = ?, payment_note = ?,
                           source = ?, bank_account = ?, student = ?, payment_method = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    (
                        rec["description"],
                        rec["payer_name"],
                        rec["reference"],
                        rec["payment_note"],
                        rec["source"],
                        rec.get("bank_account", ""),
                        rec.get("student", ""),
                        rec.get("payment_method", "Direct Deposit"),
                        datetime.now().isoformat(),
                        existing["id"],
                    ),
                )
            updated += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def get_all_transactions() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC, amount DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Whitelisted columns for any "set arbitrary field" helper. Anything outside
# this set must use a dedicated function — no string-built UPDATEs.
_USER_EDITABLE_FIELDS = {"status", "payment_method", "student"}


def update_transaction_field(row_id: int, field: str, value: str):
    if field not in _USER_EDITABLE_FIELDS:
        raise ValueError(f"Cannot update field: {field}")
    conn = get_connection()
    # Field name comes only from the whitelist above, so this is safe.
    conn.execute(f"UPDATE transactions SET {field} = ? WHERE id = ?", (value, row_id))
    conn.commit()
    conn.close()


def bulk_update_fields(
    row_ids: list[int],
    student: str | None = None,
    status: str | None = None,
    payment_method: str | None = None,
) -> int:
    """Update one or more whitelisted fields on the given rows in a single transaction.

    Returns the number of rows touched. Pass None for any field to leave it alone.
    """
    if not row_ids:
        return 0
    # Build the SET clause from explicit branches — never from caller-supplied keys.
    set_parts: list[str] = []
    params: list = []
    if student is not None:
        set_parts.append("student = ?")
        params.append(student)
    if status is not None:
        set_parts.append("status = ?")
        params.append(status)
    if payment_method is not None:
        set_parts.append("payment_method = ?")
        params.append(payment_method)
    if not set_parts:
        return 0
    set_parts.append("updated_at = ?")
    params.append(datetime.now().isoformat())

    placeholders = ",".join("?" * len(row_ids))
    sql = f"UPDATE transactions SET {', '.join(set_parts)} WHERE id IN ({placeholders})"
    conn = get_connection()
    conn.execute(sql, params + [int(r) for r in row_ids])
    conn.commit()
    conn.close()
    return len(row_ids)


def bulk_update_status(row_ids: list[int], status: str):
    bulk_update_fields(row_ids, status=status)


def set_upload_amount(row_id: int, upload_amount: float, upload_description: str, status: str = "OK to Upload") -> None:
    """Set the agent-deduction upload override fields and flip status."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET upload_amount = ?, upload_description = ?, status = ?, updated_at = ? WHERE id = ?",
        (
            float(upload_amount),
            upload_description,
            status,
            datetime.now().isoformat(),
            int(row_id),
        ),
    )
    conn.commit()
    conn.close()


def record_axcelerate_post(
    row_id: int,
    transaction_id: str,
    invoice_id: str | None,
    new_status: str,
) -> None:
    """Persist the Axcelerate TRANSACTIONID/INVOICEID returned by a successful POST.

    Called by bulk_payment.py BEFORE flipping the status so that, even if the
    process dies between this write and the status flip, a future re-run sees
    the populated transaction_id and skips the row instead of double-posting.
    """
    conn = get_connection()
    conn.execute(
        """UPDATE transactions
           SET axcelerate_transaction_id = ?, axcelerate_invoice_id = ?,
               status = ?, updated_at = ?
           WHERE id = ?""",
        (
            str(transaction_id),
            str(invoice_id) if invoice_id else None,
            new_status,
            datetime.now().isoformat(),
            int(row_id),
        ),
    )
    conn.commit()
    conn.close()


def mark_check_manually(row_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET status = ?, updated_at = ? WHERE id = ?",
        ("Check Manually", datetime.now().isoformat(), int(row_id)),
    )
    conn.commit()
    conn.close()


def delete_all_transactions():
    """Delete all transactions from the database."""
    conn = get_connection()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()


def get_agent_profiles() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM agent_profiles ORDER BY agent_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_agent_profile(agent_name: str, commission_rate: float, admin_fee_waiver: bool, bonus_eligible: bool, default_bonus: float):
    conn = get_connection()
    conn.execute(
        """INSERT INTO agent_profiles (agent_name, commission_rate, admin_fee_waiver, bonus_eligible, default_bonus)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(agent_name) DO UPDATE SET
               commission_rate = excluded.commission_rate,
               admin_fee_waiver = excluded.admin_fee_waiver,
               bonus_eligible = excluded.bonus_eligible,
               default_bonus = excluded.default_bonus""",
        (agent_name.strip(), commission_rate, int(admin_fee_waiver), int(bonus_eligible), default_bonus),
    )
    conn.commit()
    conn.close()


def delete_agent_profile(agent_name: str):
    conn = get_connection()
    conn.execute("DELETE FROM agent_profiles WHERE agent_name = ?", (agent_name,))
    conn.commit()
    conn.close()


def get_stats(direction: str = "all") -> dict:
    """Get transaction stats. direction: 'all', 'received' (amount>0), or 'spent' (amount<0)."""
    conn = get_connection()
    if direction == "received":
        where = " AND amount > 0"
    elif direction == "spent":
        where = " AND amount < 0"
    else:
        where = ""
    total = conn.execute(f"SELECT COUNT(*) FROM transactions WHERE 1=1{where}").fetchone()[0]
    unreconciled = conn.execute(
        f"SELECT COUNT(*) FROM transactions WHERE status = 'Unreconciled'{where}"
    ).fetchone()[0]
    unreconciled_amount = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'Unreconciled'{where}"
    ).fetchone()[0]
    reconciled_amount = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'Axcelerate Updated'{where}"
    ).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "unreconciled": unreconciled,
        "reconciled": total - unreconciled,
        "unreconciled_amount": abs(unreconciled_amount),
        "reconciled_amount": abs(reconciled_amount),
    }
