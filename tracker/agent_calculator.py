"""
Agent Commission Calculator.

Calculates expected payment amounts for education agent deductions,
factoring in commission rates, GST, admin fee waivers, and bonuses.

Commission is only charged on tuition fees (not admin or material fees).
GST of 10% is applied on top of the commission.
Top-tier agents may also pre-deduct admin fee waivers and bonuses.
"""


def calculate_agent_payment(
    tuition_fee: float,
    admin_fee: float = 0.0,
    material_fee: float = 0.0,
    commission_rate: float = 0.30,
    admin_fee_waiver: bool = False,
    bonus: float = 0.0,
) -> dict:
    """Calculate the expected payment after agent deductions.

    Args:
        tuition_fee: Tuition fee amount (commission-eligible).
        admin_fee: Admin fee amount (not commission-eligible).
        material_fee: Material fee amount (not commission-eligible).
        commission_rate: Agent commission rate (e.g. 0.30, 0.35, 0.40).
        admin_fee_waiver: If True, agent deducts the admin fee.
        bonus: Bonus amount the agent pre-deducts.

    Returns:
        dict with full breakdown of the calculation.
    """
    # Commission is only on tuition fee
    commission = tuition_fee * commission_rate
    gst_on_commission = commission * 0.10
    total_commission = commission + gst_on_commission

    # Admin fee waiver: agent deducts the admin fee from payment
    waiver_amount = admin_fee if admin_fee_waiver else 0.0

    # Total agent deduction
    total_deduction = total_commission + waiver_amount + bonus

    # Invoice total (what the student owes)
    invoice_total = tuition_fee + admin_fee + material_fee

    # Expected payment = invoice total minus what the agent keeps
    expected_payment = invoice_total - total_deduction

    return {
        "tuition_fee": tuition_fee,
        "admin_fee": admin_fee,
        "material_fee": material_fee,
        "invoice_total": invoice_total,
        "commission_rate": commission_rate,
        "commission": round(commission, 2),
        "gst_on_commission": round(gst_on_commission, 2),
        "total_commission": round(total_commission, 2),
        "admin_fee_waiver": waiver_amount,
        "bonus": bonus,
        "total_deduction": round(total_deduction, 2),
        "expected_payment": round(expected_payment, 2),
    }


def verify_payment(
    actual_payment: float,
    tuition_fee: float,
    admin_fee: float = 0.0,
    material_fee: float = 0.0,
    commission_rate: float = 0.30,
    admin_fee_waiver: bool = False,
    bonus: float = 0.0,
) -> dict:
    """Verify an agent payment against expected amount.

    Returns the calculation breakdown plus the discrepancy.
    """
    result = calculate_agent_payment(
        tuition_fee=tuition_fee,
        admin_fee=admin_fee,
        material_fee=material_fee,
        commission_rate=commission_rate,
        admin_fee_waiver=admin_fee_waiver,
        bonus=bonus,
    )
    result["actual_payment"] = actual_payment
    result["discrepancy"] = round(actual_payment - result["expected_payment"], 2)
    return result


def verify_payment_all_rates(
    actual_payment: float,
    tuition_fee: float,
    admin_fee: float = 0.0,
    material_fee: float = 0.0,
    admin_fee_waiver: bool = False,
    bonus: float = 0.0,
    rates: list = None,
) -> list[dict]:
    """Verify an agent payment against all commission rates.

    Returns a list of verification results, one per rate.
    """
    if rates is None:
        rates = [0.30, 0.35, 0.40]
    return [
        verify_payment(
            actual_payment=actual_payment,
            tuition_fee=tuition_fee,
            admin_fee=admin_fee,
            material_fee=material_fee,
            commission_rate=rate,
            admin_fee_waiver=admin_fee_waiver,
            bonus=bonus,
        )
        for rate in rates
    ]
