import sqlite3


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "tenant_name": row["tenant_name"],
        "period": row["period"],
        "status": row["status"],
        "usage_units": row["usage_units"],
        "subtotal_cents": row["subtotal_cents"],
        "tax_cents": row["tax_cents"],
        "total_cents": row["total_cents"],
        "created_at": row["created_at"],
    }


def list_invoices(
    conn: sqlite3.Connection,
    tenant_id: int,
    status: str | None = None,
    period: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict:
    rows = conn.execute(
        """
        SELECT i.*, t.name AS tenant_name
        FROM invoices i
        JOIN tenants t ON t.id = i.tenant_id
        WHERE i.tenant_id = ?
        ORDER BY i.period DESC, i.id DESC
        """,
        (tenant_id,),
    ).fetchall()
    return {"items": [_row_to_dict(row) for row in rows], "next_cursor": None}


def get_invoice(
    conn: sqlite3.Connection, tenant_id: int, invoice_id: int
) -> dict | None:
    row = conn.execute(
        """
        SELECT i.*, t.name AS tenant_name
        FROM invoices i
        JOIN tenants t ON t.id = i.tenant_id
        WHERE i.id = ?
        """,
        (invoice_id,),
    ).fetchone()
    return _row_to_dict(row) if row else None
