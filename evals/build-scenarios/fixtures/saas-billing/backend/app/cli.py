import argparse
import json
import sqlite3
from pathlib import Path

from app import billing, db, invoices, seed


def _connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = db.connect(path)
    db.init_schema(conn)
    return conn


def _tenant_id(conn: sqlite3.Connection, slug: str) -> int:
    row = conn.execute("SELECT id FROM tenants WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        raise SystemExit(f"unknown tenant: {slug}")
    return int(row["id"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="saas-billing")
    parser.add_argument("--db", default="data/saas.db")
    commands = parser.add_subparsers(dest="command", required=True)

    seed_parser = commands.add_parser("seed")
    seed_parser.add_argument("--reset", action="store_true")

    billing_parser = commands.add_parser("billing")
    billing_commands = billing_parser.add_subparsers(dest="billing_command", required=True)
    run_parser = billing_commands.add_parser("run")
    run_parser.add_argument("--period", required=True)

    invoice_parser = commands.add_parser("invoices")
    invoice_commands = invoice_parser.add_subparsers(dest="invoice_command", required=True)
    list_parser = invoice_commands.add_parser("list")
    list_parser.add_argument("--tenant", required=True)
    list_parser.add_argument("--status")
    list_parser.add_argument("--period")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument("--cursor")
    show_parser = invoice_commands.add_parser("show")
    show_parser.add_argument("--tenant", required=True)
    show_parser.add_argument("--id", type=int, required=True)

    args = parser.parse_args(argv)
    conn = _connect(args.db)

    if args.command == "seed":
        if args.reset:
            for table in ("invoice_lines", "invoices", "usage_events", "subscriptions", "plans", "tenants"):
                conn.execute(f"DELETE FROM {table}")
        seed.seed(conn)
        payload = {"seeded": True}
    elif args.command == "billing" and args.billing_command == "run":
        payload = billing.run_billing(conn, args.period)
    elif args.command == "invoices" and args.invoice_command == "list":
        payload = invoices.list_invoices(
            conn,
            _tenant_id(conn, args.tenant),
            status=args.status,
            period=args.period,
            limit=args.limit,
            cursor=args.cursor,
        )
    elif args.command == "invoices" and args.invoice_command == "show":
        payload = invoices.get_invoice(conn, _tenant_id(conn, args.tenant), args.id)
    else:
        parser.error("unknown command")
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
