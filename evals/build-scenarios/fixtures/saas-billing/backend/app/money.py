from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("1")


def micros_to_cents(micros: int) -> int:
    """Convert 1/10000-cent units to cents, rounding half up."""
    value = Decimal(micros) / Decimal(10000)
    return int(value.quantize(CENT, rounding=ROUND_HALF_UP))


def tax_cents(subtotal_cents: int, tax_rate_bps: int) -> int:
    value = Decimal(subtotal_cents) * Decimal(tax_rate_bps) / Decimal(10000)
    return int(value.quantize(CENT, rounding=ROUND_HALF_UP))
