import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    # Migration: add bank_account column if missing (existing DBs)
    try:
        conn.execute("SELECT bank_account FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN bank_account TEXT NOT NULL DEFAULT ''")
    # Migration: add student column if missing
    try:
        conn.execute("SELECT student FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN student TEXT NOT NULL DEFAULT ''")
    # Migration: add updated_at column if missing
    try:
        conn.execute("SELECT updated_at FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN updated_at TEXT")
    # Migration: add instance column if missing (MAC = default for existing rows)
    try:
        conn.execute("SELECT instance FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN instance TEXT NOT NULL DEFAULT 'MAC'")
    # Migration: add location column if missing (for Ezidebit campus segregation)
    try:
        conn.execute("SELECT location FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN location TEXT NOT NULL DEFAULT ''")
    # Migration: add upload_amount column if missing (for agent deduction full amount)
    try:
        conn.execute("SELECT upload_amount FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN upload_amount REAL")
    # Migration: add upload_description column if missing (for agent deduction description)
    try:
        conn.execute("SELECT upload_description FROM transactions LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE transactions ADD COLUMN upload_description TEXT")
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


def update_transaction_field(row_id: int, field: str, value: str):
    allowed = {"status", "payment_method", "student"}
    if field not in allowed:
        raise ValueError(f"Cannot update field: {field}")
    conn = get_connection()
    conn.execute(f"UPDATE transactions SET {field} = ? WHERE id = ?", (value, row_id))
    conn.commit()
    conn.close()


def bulk_update_status(row_ids: list[int], status: str):
    if not row_ids:
        return
    conn = get_connection()
    now = datetime.now().isoformat()
    placeholders = ",".join("?" * len(row_ids))
    conn.execute(
        f"UPDATE transactions SET status = ?, updated_at = ? WHERE id IN ({placeholders})",
        [status, now] + row_ids,
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
