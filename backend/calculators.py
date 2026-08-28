"""
calculators.py
Deterministic financial engine — Section 3 of the system spec.
NO LLM involvement anywhere in this file. Pure arithmetic only.
"""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field


MARGIN_FRACTION = Decimal("0.10")
LOAN_FRACTION = Decimal("0.90")

TIER_MICRO = "MICRO_FINANCE"
TIER_TERM = "TERM_LOAN"


@dataclass
class QuarterEntry:
    quarter: int
    phase: str  # "MORATORIUM" | "AMORTIZATION"
    principal: Decimal
    interest: Decimal
    total: Decimal


@dataclass
class LoanStructure:
    margin_capital: Decimal
    total_project_cost: Decimal
    loan_amount: Decimal
    scheme_tier: str
    scheme_name: str
    interest_rate_pa: Decimal
    tenure_years: int
    moratorium_months: int
    schedule: list = field(default_factory=list)


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def structure_loan(margin_capital) -> LoanStructure:
    """
    Implements the deterministic scheme-routing decision tree exactly as
    specified in Section 3 of the system design.
    """
    margin_capital = Decimal(str(margin_capital))
    total_project_cost = margin_capital / MARGIN_FRACTION
    raw_loan = total_project_cost * LOAN_FRACTION

    if total_project_cost <= Decimal("140000"):
        tier = TIER_MICRO
        scheme_name = "Micro Finance Scheme"
        ceiling = Decimal("125000")
        rate = Decimal("6.5")
        tenure_years = 3
        total_quarters = 12
        moratorium_quarters = 1
    elif total_project_cost <= Decimal("5000000"):
        tier = TIER_TERM
        scheme_name = "Term Loan Scheme"
        ceiling = Decimal("4500000")
        rate = Decimal("8.0")
        tenure_years = 7
        total_quarters = 28
        moratorium_quarters = 2
    else:
        # Outside standard State Channelizing Agency ceiling.
        tier = "OUT_OF_RANGE"
        scheme_name = "Exceeds standard SCA ceiling — route to project finance"
        ceiling = raw_loan
        rate = Decimal("8.0")
        tenure_years = 7
        total_quarters = 28
        moratorium_quarters = 2

    loan_amount = min(raw_loan, ceiling)
    active_quarters = total_quarters - moratorium_quarters
    quarterly_rate = rate / (Decimal("4") * Decimal("100"))
    principal_per_quarter = loan_amount / Decimal(active_quarters)

    schedule = []
    for q in range(1, moratorium_quarters + 1):
        interest = loan_amount * quarterly_rate
        schedule.append(QuarterEntry(
            quarter=q, phase="MORATORIUM",
            principal=Decimal("0.00"), interest=_round(interest), total=_round(interest)
        ))

    for k in range(1, active_quarters + 1):
        principal_remaining = loan_amount - (Decimal(k - 1) * principal_per_quarter)
        interest = principal_remaining * quarterly_rate
        total = principal_per_quarter + interest
        schedule.append(QuarterEntry(
            quarter=moratorium_quarters + k, phase="AMORTIZATION",
            principal=_round(principal_per_quarter), interest=_round(interest), total=_round(total)
        ))

    return LoanStructure(
        margin_capital=_round(margin_capital),
        total_project_cost=_round(total_project_cost),
        loan_amount=_round(loan_amount),
        scheme_tier=tier,
        scheme_name=scheme_name,
        interest_rate_pa=rate,
        tenure_years=tenure_years,
        moratorium_months=moratorium_quarters * 3,
        schedule=schedule,
    )


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Fallback spatial distance calc when PostGIS/GDAL is unavailable."""
    from math import radians, sin, cos, asin, sqrt
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def saturation_index(count: int, radius_km: float) -> dict:
    from math import pi
    density = count / (pi * radius_km ** 2)
    if count == 0:
        level = "LOW"
    elif count <= 2:
        level = "MODERATE"
    elif count <= 5:
        level = "HIGH"
    else:
        level = "OVERSATURATED"
    return {"density_per_sq_km": round(density, 5), "level": level}
