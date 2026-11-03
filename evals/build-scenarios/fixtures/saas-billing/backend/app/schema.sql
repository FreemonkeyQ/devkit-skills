CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    tax_rate_bps INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plans (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    monthly_price_cents INTEGER NOT NULL,
    included_units INTEGER NOT NULL,
    overage_micros_per_unit INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    plan_code TEXT NOT NULL REFERENCES plans(code),
    status TEXT NOT NULL,
    current_period_start TEXT NOT NULL,
    current_period_end TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    metric TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    period TEXT NOT NULL,
    status TEXT NOT NULL,
    subtotal_cents INTEGER NOT NULL,
    tax_cents INTEGER NOT NULL,
    total_cents INTEGER NOT NULL,
    usage_units INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (tenant_id, period)
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_tenant_time ON usage_events(tenant_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant_period ON invoices(tenant_id, period, id);
