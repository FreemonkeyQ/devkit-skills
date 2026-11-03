import sqlite3
from datetime import datetime, timezone


def period_end(period: str) -> str:
    year, month = (int(part) for part in period.split("-"))
    if month == 12:
        return f"{year + 1}-01-01"
    return f"{year}-{month + 1:02d}-01"


def run_billing(conn: sqlite3.Connection, period: str) -> dict:
    """Generate one invoice per active subscription for the given period."""
    start = f"{period}-01"
    end = period_end(period)
    subscriptions = conn.execute(
        """
        SELECT s.tenant_id, s.plan_code, t.tax_rate_bps,
               p.monthly_price_cents, p.included_units, p.overage_micros_per_unit
        FROM subscriptions s
        JOIN tenants t ON t.id = s.tenant_id
        JOIN plans p ON p.code = s.plan_code
        WHERE s.status = 'ACTIVE'
        """
    ).fetchall()

    created: list[int] = []
    for subscription in subscriptions:
        usage = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS total FROM usage_events "
            "WHERE tenant_id = ? AND recorded_at >= ? AND recorded_at < ?",
            (subscription["tenant_id"], start, end),
        ).fetchone()["total"]
        overage_units = max(0, usage - subscription["included_units"])
        overage_cents = int(
            overage_units * subscription["overage_micros_per_unit"] / 10000
        )
        subtotal = subscription["monthly_price_cents"] + overage_cents
        tax = int(subtotal * subscription["tax_rate_bps"] / 10000)
        cursor = conn.execute(
            """
            INSERT INTO invoices
                (tenant_id, period, status, subtotal_cents, tax_cents,
                 total_cents, usage_units, created_at)
            VALUES (?, ?, 'OPEN', ?, ?, ?, ?, ?)
            """,
            (
                subscription["tenant_id"],
                period,
                subtotal,
                tax,
                subtotal + tax,
                usage,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        invoice_id = int(cursor.lastrowid)
        conn.execute(
            "INSERT INTO invoice_lines (invoice_id, kind, description, amount_cents) "
            "VALUES (?, 'plan', ?, ?)",
            (invoice_id, f"{subscription['plan_code']} monthly fee", subscription["monthly_price_cents"]),
        )
        if overage_cents:
            conn.execute(
                "INSERT INTO invoice_lines (invoice_id, kind, description, amount_cents) "
                "VALUES (?, 'overage', 'Usage overage', ?)",
                (invoice_id, overage_cents),
            )
        created.append(invoice_id)

    conn.commit()
    return {"created": len(created), "existing": 0, "invoice_ids": created}
