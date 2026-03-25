"""
Bank transaction reconciliation engine.

Implements the classification rules from axcelerate-reconcile.md:
- Student identification (Student ID → MAC ID → Name → Name+Info → Unknown)
- Payment method classification (Direct Deposit, Agent Deduction, Direct Debit, Stripe, Internal Transfer)
"""

import re

# --- Known agents (PAYMENT FROM pattern) ---
# Maps agent name fragment (lowercase) → column preference for student info
# "h" = Col H (Column7), "i" = Col I (Column8), "hi" = try H then I
PAYMENT_FROM_AGENTS: dict[str, str] = {
    "onepoint": "h",
    "edunetwork": "i",
    "spot on global": "hi",
    "ehub international": "i",
    "e-colink": "h",
    "drm": "h",
    "migrationarcadia": "h",
    "qualy pay": "i",
    "spark group international": "h",
    "primo group australia": "h",
    "top notch study and visa": "i",
    "new era international": "i",
    "student vibes": "h",
    "clear eyed": "i",
    "vanesa correa mejia": "h",
    "ankita chopra": "i",
    "ankit arora": "i",
    "angela sthefania carrasco": "i",
    "justice fami": "h",
    "kiran": "i",
    "acelegalpartners": "i",
    "royal international migrat": "hi",
    "fast track consultancy": "hi",
    "bajwa consultant": "d",
}

# TRANSFER FROM agents — student info is extracted from Col D (description)
TRANSFER_FROM_AGENTS: list[str] = [
    "aussizz",
    "shabbir iqbal",
    "cba",
    "g8m8",
    "great mate",
    "asia pacific edu",
    "foad matrix",
    "bajwa consultant",
    "marco aurelio",
]

# Organization keywords that indicate Agent Deduction
ORG_KEYWORDS: list[str] = [
    "pty", "ltd", "international", "group", "global",
    "migration", "consultancy", "consultant", "consultants",
    "education", "providen",
]

# Fee/noise words to strip from student names
FEE_WORDS: set[str] = {
    "college", "fees", "fee", "tuition", "payment", "deposit", "coe",
    "enrolment", "enrollment", "certificate", "cert", "iii", "iv",
    "advance", "diploma", "installment", "instalment", "initial",
    "school", "course", "material", "studies", "macallan",
    "first", "second", "split", "trade", "emi", "req",
    "wall", "floor", "tiling", "dhm", "2nd", "3rd", "1st",
    "student", "id", "sid", "pay", "ref", "inv",
    "term", "transfer", "receipt", "stud",
}

# Macallan entity name fragments (Col F) — these are NOT agents
MACALLAN_ENTITIES: list[str] = [
    "macallan education",
    "macallan college",
    "macall",
    "macalla",
    "mavallan",
]

# Student ID regex: 8-digit number starting with 1
STUDENT_ID_RE = re.compile(r"(?<!\d)(1\d{7})(?!\d)")

# MAC ID regex: MAC + optional space + 4 digits
MAC_ID_RE = re.compile(r"\bMAC\s?(\d{4})\b", re.IGNORECASE)


def _is_macallan_entity(text: str) -> bool:
    """Check if text is a Macallan entity name (not an external org)."""
    if not text:
        return True  # empty = assume Macallan
    lower = text.lower().strip()
    return any(m in lower for m in MACALLAN_ENTITIES)


def _clean_student_name(text: str) -> str:
    """Remove fee/noise words and prefixes from a student name."""
    if not text:
        return ""
    text = text.strip()
    # Remove MR/MRS/MS prefix
    text = re.sub(r"^(MR|MRS|MS|MISS)\s+", "", text, flags=re.IGNORECASE)
    # Remove underscores
    text = text.replace("_", " ")
    # Remove leading/trailing digits and punctuation
    text = re.sub(r"^\d+\s*", "", text)
    text = text.strip("- .,;:()")
    # Remove fee words
    words = text.split()
    cleaned = []
    for w in words:
        if w.lower().strip(".,;:-()") in FEE_WORDS:
            continue
        # Skip pure numbers
        if re.match(r"^\d+$", w.strip(".,;:-")):
            continue
        # Skip date-like patterns
        if re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", w):
            continue
        cleaned.append(w)
    result = " ".join(cleaned).strip("- .,;:()")
    return result


def _extract_student_id(text: str) -> str | None:
    """Extract 8-digit student ID starting with 1 from text."""
    if not text:
        return None
    matches = STUDENT_ID_RE.findall(text)
    if matches:
        return matches[-1]  # Last match — student IDs tend to come after REF: etc.
    return None


def _extract_mac_id(text: str) -> str | None:
    """Extract MAC ID from text, normalizing spaces."""
    if not text:
        return None
    m = MAC_ID_RE.search(text)
    if m:
        return f"MAC{m.group(1)}"
    return None


def _is_known_payment_agent(text: str) -> str | None:
    """Check if text matches a known PAYMENT FROM agent. Returns the column preference."""
    if not text:
        return None
    lower = text.lower()
    for agent, pref in PAYMENT_FROM_AGENTS.items():
        if agent in lower:
            return pref
    return None


def _is_transfer_from_agent(description: str) -> bool:
    """Check if description matches a TRANSFER FROM agent pattern."""
    if not description:
        return False
    lower = description.lower()
    if "transfer from" not in lower:
        return False
    for agent in TRANSFER_FROM_AGENTS:
        if agent in lower:
            return True
    return False


def _has_org_keyword(text: str) -> bool:
    """Check if text contains organization keywords suggesting Agent Deduction."""
    if not text:
        return False
    lower = text.lower()
    for kw in ORG_KEYWORDS:
        if kw in lower:
            return True
    return False


def _extract_student_from_agent(description: str, payer: str, col_h: str, col_i: str, agent_pref: str | None) -> str:
    """Extract student info for agent payments based on agent-specific column preferences."""

    # First: always try student ID from all columns
    all_text = f"{description} {col_h} {col_i}"
    sid = _extract_student_id(all_text)
    if sid:
        return sid

    # MAC ID check
    mac = _extract_mac_id(all_text)
    if mac:
        return mac

    # Agent-specific column preference
    if agent_pref == "i" and col_i:
        # Edunetwork-specific: "NP[amount] - [ref] - [Student Name]"
        edunet_match = re.match(r"NP\d+\s*-\s*\d+\s*-\s*(.+)", col_i)
        if edunet_match:
            name = _clean_student_name(edunet_match.group(1))
            if name and len(name) > 1:
                return name
            # NP format matched but name truncated — don't fall through to garbage
            return "Unknown"
        # Catch truncated Edunetwork refs like "NP962.50" (amount only, no student)
        if re.match(r"NP\d", col_i):
            return "Unknown"
        name = _clean_student_name(col_i)
        if name and len(name) > 1:
            return name
    if agent_pref == "h" and col_h:
        name = _clean_student_name(col_h)
        if name and len(name) > 1:
            return name
    if agent_pref == "hi":
        for col in [col_h, col_i]:
            name = _clean_student_name(col)
            if name and len(name) > 1:
                return name
    if agent_pref == "d":
        # Extract from description after agent name pattern
        m = re.search(r"(?:TRANSFER|PAYMENT)\s+FROM\s+\S+\s+(.+)", description, re.IGNORECASE)
        if m:
            name = _clean_student_name(m.group(1))
            if name and len(name) > 1:
                return name

    # Generic fallback: try col_i then col_h
    for col in [col_i, col_h]:
        name = _clean_student_name(col)
        if name and len(name) > 1:
            return name

    return "Unknown"


def _extract_transfer_student(description: str) -> str:
    """Extract student info from TRANSFER FROM description."""
    # Try student ID first
    sid = _extract_student_id(description)
    if sid:
        return sid

    # Try ID:[8digits] pattern (Aussizz)
    m = re.search(r"ID[:\s]*(1\d{7})", description, re.IGNORECASE)
    if m:
        return m.group(1)

    # Extract name after agent name — usually after multiple spaces
    # Pattern: TRANSFER FROM <AGENT>   <STUDENT NAME>
    m = re.search(r"TRANSFER\s+FROM\s+\S+\s{2,}(.+?)(?:\s{2,}|$)", description, re.IGNORECASE)
    if m:
        name = _clean_student_name(m.group(1))
        if name and len(name) > 1:
            return name

    # Fallback: everything after TRANSFER FROM <2-word agent>
    m = re.search(r"TRANSFER\s+FROM\s+\w+\s+\w+\s+(.+)", description, re.IGNORECASE)
    if m:
        name = _clean_student_name(m.group(1))
        if name and len(name) > 1:
            return name

    return "Unknown"


def classify_payment_method(
    description: str,
    payer: str,
    payee: str,
    col_h: str,
    col_i: str,
) -> str:
    """Classify the payment method for a transaction.

    Returns one of: Direct Deposit, Agent Deduction, Direct Debit, Stripe, Internal Transfer
    """
    all_text = f"{description} {payer} {payee} {col_h} {col_i}".upper()

    # 1. Stripe
    if "STRIPE" in all_text:
        return "Stripe"

    # 2. Direct Debit (Ezidebit)
    if "EZIDEBIT" in all_text:
        return "Direct Debit"

    # 3. Internal Transfer (FUNDS TFER can appear in description or reference columns)
    if "FUNDS TFER" in all_text:
        return "Internal Transfer"

    # 4. Agent Deduction checks
    desc_upper = description.upper()

    # AGENT DEPOSIT = ATM cash deposit = Direct Deposit (NOT agent)
    if "AGENT DEPOSIT" in desc_upper:
        return "Direct Deposit"

    # Known PAYMENT FROM agents
    agent_pref = _is_known_payment_agent(payer)
    if agent_pref:
        return "Agent Deduction"
    agent_pref = _is_known_payment_agent(description)
    if agent_pref:
        return "Agent Deduction"

    # TRANSFER FROM with known agent
    if _is_transfer_from_agent(description):
        return "Agent Deduction"

    # Organization keywords in payer name
    if payer and _has_org_keyword(payer):
        return "Agent Deduction"

    # Col F (payee) is NOT a Macallan entity → external org paying = Agent Deduction
    if payee and not _is_macallan_entity(payee):
        return "Agent Deduction"

    # Payer paying for a different student (payer ≠ student in references)
    if payer and payer != "#NAME?":
        payer_words = set(payer.upper().split()[:3])
        for ref_col in [col_h, col_i]:
            if ref_col:
                ref_clean = _clean_student_name(ref_col)
                if ref_clean and len(ref_clean.split()) >= 2:
                    ref_words = set(ref_clean.upper().split()[:3])
                    # If no overlap in name words → different person paying
                    if payer_words and ref_words and not payer_words.intersection(ref_words):
                        return "Agent Deduction"

    # 5. Default: Direct Deposit
    return "Direct Deposit"


def extract_student(
    description: str,
    payer: str,
    payee: str,
    col_h: str,
    col_i: str,
    payment_method: str,
) -> str:
    """Extract student identifier from transaction columns.

    Returns: student ID, MAC ID, student name, or "Unknown"
    """
    all_cols = f"{description} {payer} {col_h} {col_i}"

    # Priority 1: Student ID (8-digit starting with 1) from all description columns
    search_cols = [col_h, col_i, description, payer]
    for col in search_cols:
        sid = _extract_student_id(col)
        if sid:
            return sid

    # Priority 2: MAC ID
    mac = _extract_mac_id(all_cols)
    if mac:
        return mac

    # Internal Transfer → Unknown
    if payment_method == "Internal Transfer":
        return "Unknown"

    # Direct Debit (Ezidebit) → Unknown (batch, needs manual reconciliation)
    if payment_method == "Direct Debit":
        return "Unknown"

    # Agent Deduction: extract student from agent-specific columns
    if payment_method == "Agent Deduction":
        # Check known agents for column preference
        agent_pref = _is_known_payment_agent(payer) or _is_known_payment_agent(description)

        # TRANSFER FROM pattern
        if "TRANSFER FROM" in description.upper():
            result = _extract_transfer_student(description)
            if result != "Unknown":
                return result
            # Also check col_h and col_i
            for col in [col_h, col_i]:
                name = _clean_student_name(col)
                if name and len(name) > 1:
                    return name
            return "Unknown"

        return _extract_student_from_agent(description, payer, col_h, col_i, agent_pref)

    # Direct Deposit / Stripe: student IS the payer
    if payment_method in ("Direct Deposit", "Stripe"):
        # #NAME? means payer name is mangled — extract from description
        if not payer or payer == "#NAME?":
            m = re.search(r"(?:PAYMENT|TRANSFER)\s+FROM\s+(?:-\s*)?(.+?)(?:\s+\d{8}|\s*$)", description, re.IGNORECASE)
            if m:
                name = _clean_student_name(m.group(1))
                if name and len(name) > 1:
                    return name
            return "Unknown"

        # Check if payer is paying for someone else (col_h/col_i has a different name)
        # If so, use the references
        payer_clean = _clean_student_name(payer)
        for ref_col in [col_h, col_i]:
            if ref_col:
                ref_clean = _clean_student_name(ref_col)
                if ref_clean and len(ref_clean.split()) >= 2:
                    payer_words = set(payer_clean.upper().split()[:3]) if payer_clean else set()
                    ref_words = set(ref_clean.upper().split()[:3])
                    if payer_words and ref_words and not payer_words.intersection(ref_words):
                        # Different person — use reference name
                        return ref_clean

        return payer_clean if payer_clean else "Unknown"

    return "Unknown"


def reconcile_transaction(
    description: str,
    payer: str,
    payee: str,
    col_h: str,
    col_i: str,
    amount: float,
) -> dict:
    """Reconcile a single transaction row.

    Args:
        description: Col D (Column3) - primary description
        payer: Col E (Column4) - payer name
        payee: Col F (Column5) - payee/entity name
        col_h: Col H (Column7) - reference field 1
        col_i: Col I (Column8) - reference field 2
        amount: Col C (Column2) - transaction amount

    Returns:
        dict with 'student' and 'payment_method' keys
    """
    # Only reconcile positive (incoming) amounts
    if amount <= 0:
        return {"student": "", "payment_method": ""}

    # Clean inputs
    description = (description or "").strip()
    payer = (payer or "").strip()
    payee = (payee or "").strip()
    col_h = (col_h or "").strip()
    col_i = (col_i or "").strip()

    payment_method = classify_payment_method(description, payer, payee, col_h, col_i)
    student = extract_student(description, payer, payee, col_h, col_i, payment_method)

    return {"student": student, "payment_method": payment_method}
