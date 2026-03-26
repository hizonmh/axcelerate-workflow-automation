import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from database import init_db, upsert_transactions, get_all_transactions, bulk_update_status
from parsers import detect_and_parse

# --- Page config ---
st.set_page_config(page_title="Bank Transaction Tracker", layout="wide")
init_db()

PAYMENT_METHODS = ["Direct Deposit", "Agent Deduction", "Direct Debit", "Stripe", "Internal Transfer"]

# --- Page header ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "table_key" not in st.session_state:
    st.session_state.table_key = 0

st.markdown("### Bank Transaction Tracker")

# --- Import section (expandable) ---
with st.expander("Import Transactions"):
    uploaded_files = st.file_uploader(
        "Drop bank CSV or Xero Excel files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files and st.button("Import Files", type="primary"):
        total_inserted = total_updated = total_skipped = 0
        for f in uploaded_files:
            try:
                records = detect_and_parse(f.name, f.read())
                result = upsert_transactions(records)
                total_inserted += result["inserted"]
                total_updated += result["updated"]
                total_skipped += result["skipped"]
                st.success(f"**{f.name}**: {result['inserted']} new, {result['updated']} updated, {result['skipped']} skipped")
            except Exception as e:
                st.error(f"**{f.name}**: {e}")
        st.session_state.uploader_key += 1
        st.rerun()

# --- Upload to Axcelerate section ---
def _upload_panel(instance_label: str, instance_code: str):
    """Render upload counts and button for one Axcelerate instance."""
    from database import get_connection
    conn = get_connection()
    ok_count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE status = 'OK to Upload' AND instance = ?",
        (instance_code,),
    ).fetchone()[0]
    ok_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'OK to Upload' AND instance = ?",
        (instance_code,),
    ).fetchone()[0]
    conn.close()

    running_key = f"upload_running_{instance_code}"
    output_key = f"upload_output_{instance_code}"
    if running_key not in st.session_state:
        st.session_state[running_key] = False
    if output_key not in st.session_state:
        st.session_state[output_key] = None

    if ok_count == 0:
        st.caption(f"**{instance_label}**: No transactions ready to upload.")
    else:
        st.markdown(f"**{instance_label}**: {ok_count} txn(s) — **${ok_total:,.2f}**")
        if st.button(f"Upload {instance_label}", type="primary", key=f"upload_btn_{instance_code}",
                      disabled=st.session_state[running_key]):
            st.session_state[running_key] = True
            script_path = os.path.join(os.path.dirname(__file__), "..", "bulk_payment.py")
            with st.spinner(f"Uploading {instance_label} payments..."):
                result = subprocess.run(
                    [sys.executable, script_path, "--instance", instance_code],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(script_path),
                    timeout=600,
                )
            st.session_state[running_key] = False
            st.session_state[output_key] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            st.session_state.table_key += 1
            st.rerun()

    if st.session_state[output_key] is not None:
        output = st.session_state[output_key]
        if output["returncode"] == 0:
            st.success(f"{instance_label} upload completed successfully.")
        else:
            st.error(f"{instance_label} upload finished with errors (exit code {output['returncode']}).")
        if output["stdout"]:
            st.code(output["stdout"], language="text")
        if output["stderr"]:
            st.caption("Errors:")
            st.code(output["stderr"], language="text")
        if st.button(f"Clear {instance_label} output", key=f"clear_{instance_code}"):
            st.session_state[output_key] = None
            st.rerun()


with st.expander("Upload to Axcelerate"):
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        _upload_panel("MAC", "MAC")
    with col_u2:
        _upload_panel("NECGC", "NECGC")
    col_u3, _ = st.columns(2)
    with col_u3:
        _upload_panel("NECTECH", "NEC")

# Load data
all_txns = get_all_transactions()
if not all_txns:
    st.info("No transactions yet. Expand 'Import Transactions' above to upload a bank CSV or Xero Excel file.")
    st.stop()

df = pd.DataFrame(all_txns)

# Split by instance and direction
_instance_col = df["instance"] if "instance" in df.columns else pd.Series("MAC", index=df.index)
mac_df = df[_instance_col == "MAC"]
necgc_df = df[_instance_col == "NECGC"]
nec_df = df[_instance_col == "NEC"]

mac_received = mac_df[mac_df["amount"] > 0].copy()
mac_spent = mac_df[mac_df["amount"] < 0].copy()
necgc_received = necgc_df[necgc_df["amount"] > 0].copy()
necgc_spent = necgc_df[necgc_df["amount"] < 0].copy()
nec_received = nec_df[nec_df["amount"] > 0].copy()
nec_spent = nec_df[nec_df["amount"] < 0].copy()


def render_transaction_table(tab_df: pd.DataFrame, tab_key: str):
    """Render filters, data editor, and bulk actions for a transaction set."""
    if tab_df.empty:
        st.info("No transactions in this category.")
        return

    # --- Filters ---
    STATUS_OPTIONS = ["Unreconciled", "OK to Upload", "Axcelerate Updated", "Unallocated", "Check Manually", "No Action"]
    STATUS_DEFAULTS = {"Unreconciled", "OK to Upload", "Unallocated", "Check Manually"}
    STUDENT_OPTIONS = ["Has Student", "Unknown", "Empty"]

    def popover_filter(label, options, tab_key, prefix, defaults=None):
        """Compact filter: popover button showing 'N selected', checkboxes inside."""
        init_key = f"_init_{prefix}_{tab_key}"
        if init_key not in st.session_state:
            for opt in options:
                st.session_state[f"_{prefix}_{tab_key}_{opt}"] = opt in defaults if defaults else False
            st.session_state[init_key] = True
        selected = [opt for opt in options if st.session_state.get(f"_{prefix}_{tab_key}_{opt}", False)]
        n = len(selected)
        if n == 0 or n == len(options):
            summary = "All"
        else:
            summary = f"{n} selected"
        with st.popover(f"**{label}:** {summary}"):
            for opt in options:
                st.checkbox(opt, key=f"_{prefix}_{tab_key}_{opt}")
        return selected if 0 < n < len(options) else []

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1, 1, 1, 1, 2])

    with col_f1:
        status_filter = popover_filter("Status", STATUS_OPTIONS, tab_key, "sf", defaults=STATUS_DEFAULTS)
    with col_f2:
        method_filter = popover_filter("Method", PAYMENT_METHODS, tab_key, "mf")
    with col_f3:
        account_options = sorted(tab_df["bank_account"].dropna().unique().tolist())
        account_filter = popover_filter("Account", account_options, tab_key, "af")
    with col_f4:
        student_filter = popover_filter("Student", STUDENT_OPTIONS, tab_key, "stf")
    with col_f5:
        search = st.text_input("Search (name, student, reference, description)", key=f"search_{tab_key}")

    # Apply filters (empty list = show all)
    filtered = tab_df.copy()
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if method_filter:
        filtered = filtered[filtered["payment_method"].isin(method_filter)]
    if account_filter:
        filtered = filtered[filtered["bank_account"].isin(account_filter)]
    if student_filter:
        masks = []
        if "Has Student" in student_filter:
            masks.append((filtered["student"] != "") & (filtered["student"] != "Unknown"))
        if "Unknown" in student_filter:
            masks.append(filtered["student"] == "Unknown")
        if "Empty" in student_filter:
            masks.append(filtered["student"] == "")
        if masks:
            combined = masks[0]
            for m in masks[1:]:
                combined = combined | m
            filtered = filtered[combined]
    if search:
        search_lower = search.lower()
        mask = (
            filtered["payer_name"].str.lower().str.contains(search_lower, na=False)
            | filtered["student"].str.lower().str.contains(search_lower, na=False)
            | filtered["reference"].str.lower().str.contains(search_lower, na=False)
            | filtered["description"].str.lower().str.contains(search_lower, na=False)
            | filtered["payment_note"].str.lower().str.contains(search_lower, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"Showing {len(filtered)} of {len(tab_df)} transactions")

    # --- Styled table ---
    if not filtered.empty:
        # Mark rows from the last edit batch with a dot indicator
        last_edit = filtered["updated_at"].dropna()
        last_edit_ts = last_edit.max() if not last_edit.empty else None
        filtered = filtered.copy()
        if last_edit_ts:
            filtered["_edited"] = filtered["updated_at"].apply(lambda v: "●" if v == last_edit_ts else "")
        else:
            filtered["_edited"] = ""

        display_cols = ["_edited", "status", "source", "bank_account", "student", "date", "amount", "payment_method", "payer_name", "reference", "description"]

        view_df = filtered[display_cols].reset_index(drop=True)
        view_df.columns = ["⟳", "Status", "Source", "Account", "Student", "Date", "Amount", "Payment Method", "Payer", "Reference", "Description"]

        def highlight_row(row):
            if row["Status"] == "Axcelerate Updated":
                return ["background-color: #d4edda"] * len(row)
            if row["Status"] == "No Action":
                return ["background-color: #e0e0e0"] * len(row)
            return [""] * len(row)

        styled = view_df.style.apply(highlight_row, axis=1).format({"Amount": "${:,.2f}"})

        event = st.dataframe(
            styled,
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key=f"txn_view_{tab_key}_{st.session_state.table_key}",
        )

        # --- Edit selected rows ---
        selected_indices = []
        if hasattr(event, "selection") and event.selection:
            selected_indices = event.selection.rows

        if selected_indices:
            selected_filtered = filtered.iloc[selected_indices]
            selected_ids = selected_filtered["id"].tolist()

            st.caption(f"{len(selected_indices)} row(s) selected")

            col_e1, col_e2, col_e3, col_e4 = st.columns([2, 2, 2, 1])
            with col_e1:
                new_student = st.text_input("Set Student", key=f"edit_student_{tab_key}")
            with col_e2:
                new_status = st.selectbox(
                    "Set Status",
                    ["(no change)", "Unreconciled", "OK to Upload", "Axcelerate Updated", "Unallocated", "Check Manually", "No Action"],
                    key=f"edit_status_{tab_key}",
                )
            with col_e3:
                new_method = st.selectbox(
                    "Set Payment Method",
                    ["(no change)"] + PAYMENT_METHODS,
                    key=f"edit_method_{tab_key}",
                )
            with col_e4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Apply", type="primary", use_container_width=True, key=f"apply_edit_{tab_key}"):
                    from database import get_connection
                    from datetime import datetime
                    conn = get_connection()
                    changes = 0
                    now = datetime.now().isoformat()
                    for rid in selected_ids:
                        updates = []
                        params = []
                        if new_student:
                            updates.append("student = ?")
                            params.append(new_student)
                        if new_status != "(no change)":
                            updates.append("status = ?")
                            params.append(new_status)
                        if new_method != "(no change)":
                            updates.append("payment_method = ?")
                            params.append(new_method)
                        if updates:
                            updates.append("updated_at = ?")
                            params.append(now)
                            params.append(int(rid))
                            conn.execute(
                                f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?",
                                params,
                            )
                            changes += 1
                    conn.commit()
                    conn.close()
                    if changes:
                        st.toast(f"Updated {changes} transaction(s)")
                        st.session_state.table_key += 1
                        st.rerun()

    # --- Bulk actions ---
    st.divider()
    col_b1, col_b2, col_b3 = st.columns([2, 2, 4])
    with col_b1:
        if st.button("Mark ALL filtered as 'Axcelerate Updated'", use_container_width=True, key=f"bulk_reconcile_{tab_key}"):
            if not filtered.empty:
                bulk_update_status(filtered["id"].tolist(), "Axcelerate Updated")
                st.toast(f"Marked {len(filtered)} transactions as updated")
                st.session_state.table_key += 1
                st.rerun()
    with col_b2:
        if st.button("Mark ALL filtered as 'Unreconciled'", use_container_width=True, key=f"bulk_unrec_{tab_key}"):
            if not filtered.empty:
                bulk_update_status(filtered["id"].tolist(), "Unreconciled")
                st.toast(f"Marked {len(filtered)} transactions as unreconciled")
                st.session_state.table_key += 1
                st.rerun()


# --- Tabs ---
tab_mac_recv, tab_mac_spent, tab_necgc_recv, tab_necgc_spent, tab_nec_recv, tab_nec_spent = st.tabs([
    f"MAC-Received ({len(mac_received)})",
    f"MAC-Spent ({len(mac_spent)})",
    f"NECGC-Received ({len(necgc_received)})",
    f"NECGC-Spent ({len(necgc_spent)})",
    f"NECTECH-Received ({len(nec_received)})",
    f"NECTECH-Spent ({len(nec_spent)})",
])

with tab_mac_recv:
    render_transaction_table(mac_received, "mac_received")

with tab_mac_spent:
    render_transaction_table(mac_spent, "mac_spent")

with tab_necgc_recv:
    render_transaction_table(necgc_received, "necgc_received")

with tab_necgc_spent:
    render_transaction_table(necgc_spent, "necgc_spent")

with tab_nec_recv:
    render_transaction_table(nec_received, "nec_received")

with tab_nec_spent:
    render_transaction_table(nec_spent, "nec_spent")
