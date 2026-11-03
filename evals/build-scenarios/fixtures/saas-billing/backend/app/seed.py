import sqlite3

TENANTS = [
    (1, "acme", "Acme Robotics", 875),
    (2, "globex", "Globex Labs", 725),
    (3, "initech", "Initech", 0),
]

PLANS = [
    ("starter", "Starter", 4900, 1000, 12000),
    ("growth", "Growth", 19900, 5000, 3333),
]

SUBSCRIPTIONS = [
    (1, 1, "growth", "ACTIVE", "2026-10-01", "2026-11-01"),
    (2, 2, "starter", "ACTIVE", "2026-10-01", "2026-11-01"),
    (3, 3, "growth", "ACTIVE", "2026-10-01", "2026-11-01"),
]

USAGE_EVENTS = [
    (1, 1, "api_calls", 2000, "2026-10-03T10:00:00Z"),
    (2, 1, "api_calls", 3000, "2026-10-17T10:00:00Z"),
    (3, 1, "api_calls", 1200, "2026-10-28T10:00:00Z"),
    (4, 2, "api_calls", 900, "2026-10-11T10:00:00Z"),
    (5, 3, "api_calls", 5000, "2026-10-02T10:00:00Z"),
    (6, 3, "api_calls", 50, "2026-10-22T10:00:00Z"),
]

INVOICES = [
    (101, 1, "2026-09", "PAID", 20000, 1750, 21750, 5000, "2026-10-01T02:00:00Z"),
    (102, 2, "2026-09", "OPEN", 4900, 355, 5255, 900, "2026-10-01T02:00:00Z"),
    (103, 3, "2026-08", "PAID", 19900, 0, 19900, 5000, "2026-09-01T02:00:00Z"),
]

INVOICE_LINES = [
    (1001, 101, "plan", "Growth monthly fee", 19900),
    (1002, 101, "overage", "Usage overage", 100),
    (1003, 102, "plan", "Starter monthly fee", 4900),
    (1004, 103, "plan", "Growth monthly fee", 19900),
]


def seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO tenants (id, slug, name, tax_rate_bps) VALUES (?, ?, ?, ?)",
        TENANTS,
    )
    conn.executemany(
        "INSERT INTO plans (code, name, monthly_price_cents, included_units, overage_micros_per_unit) "
        "VALUES (?, ?, ?, ?, ?)",
        PLANS,
    )
    conn.executemany(
        "INSERT INTO subscriptions (id, tenant_id, plan_code, status, current_period_start, current_period_end) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        SUBSCRIPTIONS,
    )
    conn.executemany(
        "INSERT INTO usage_events (id, tenant_id, metric, quantity, recorded_at) "
        "VALUES (?, ?, ?, ?, ?)",
        USAGE_EVENTS,
    )
    conn.executemany(
        "INSERT INTO invoices (id, tenant_id, period, status, subtotal_cents, tax_cents, total_cents, usage_units, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        INVOICES,
    )
    conn.executemany(
        "INSERT INTO invoice_lines (id, invoice_id, kind, description, amount_cents) "
        "VALUES (?, ?, ?, ?, ?)",
        INVOICE_LINES,
    )
    conn.commit()
