import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app import billing, db, invoices, seed


class HiddenBillingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = db.connect(str(Path(self.tmp.name) / "billing.db"))
        db.init_schema(self.conn)
        seed.seed(self.conn)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def _invoice_rows(self, period="2026-10"):
        rows = self.conn.execute(
            "SELECT * FROM invoices WHERE period = ? ORDER BY tenant_id", (period,)
        ).fetchall()
        return {row["tenant_id"]: row for row in rows}

    def test_amounts_use_cents_and_round_half_up(self):
        result = billing.run_billing(self.conn, "2026-10")
        self.assertEqual(result["created"], 3)
        rows = self._invoice_rows()

        acme = rows[1]
        self.assertEqual(acme["usage_units"], 6200)
        self.assertEqual(acme["subtotal_cents"], 20300)
        self.assertEqual(acme["tax_cents"], 1776)
        self.assertEqual(acme["total_cents"], 22076)

        globex = rows[2]
        self.assertEqual(globex["subtotal_cents"], 4900)
        self.assertEqual(globex["tax_cents"], 355)
        self.assertEqual(globex["total_cents"], 5255)

        initech = rows[3]
        self.assertEqual(initech["subtotal_cents"], 19917)
        self.assertEqual(initech["tax_cents"], 0)
        self.assertEqual(initech["total_cents"], 19917)

    def test_invoice_lines_match_subtotal(self):
        billing.run_billing(self.conn, "2026-10")
        rows = self.conn.execute(
            """
            SELECT i.id, i.subtotal_cents, COALESCE(SUM(l.amount_cents), 0) AS line_total
            FROM invoices i
            LEFT JOIN invoice_lines l ON l.invoice_id = i.id
            WHERE i.period = '2026-10'
            GROUP BY i.id
            """
        ).fetchall()
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["subtotal_cents"], row["line_total"])

    def test_repeated_run_is_idempotent(self):
        first = billing.run_billing(self.conn, "2026-10")
        self.assertEqual(first["created"], 3)
        invoice_count = self.conn.execute(
            "SELECT COUNT(*) AS n FROM invoices WHERE period = '2026-10'"
        ).fetchone()["n"]
        line_count = self.conn.execute(
            """
            SELECT COUNT(*) AS n FROM invoice_lines
            WHERE invoice_id IN (SELECT id FROM invoices WHERE period = '2026-10')
            """
        ).fetchone()["n"]

        second = billing.run_billing(self.conn, "2026-10")
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["existing"], 3)
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) AS n FROM invoices WHERE period = '2026-10'"
            ).fetchone()["n"],
            invoice_count,
        )
        self.assertEqual(
            self.conn.execute(
                """
                SELECT COUNT(*) AS n FROM invoice_lines
                WHERE invoice_id IN (SELECT id FROM invoices WHERE period = '2026-10')
                """
            ).fetchone()["n"],
            line_count,
        )

    def test_list_is_tenant_scoped_and_cursor_paginated(self):
        billing.run_billing(self.conn, "2026-10")
        acme_ids = []
        cursor = None
        for _ in range(10):
            page = invoices.list_invoices(self.conn, 1, limit=1, cursor=cursor)
            self.assertEqual(len(page["items"]), 1)
            item = page["items"][0]
            self.assertEqual(item["tenant_id"], 1)
            acme_ids.append(item["id"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
        self.assertEqual(len(acme_ids), 2)
        self.assertEqual(len(set(acme_ids)), 2)

        acme_open = invoices.list_invoices(self.conn, 1, status="OPEN")
        self.assertTrue(all(item["status"] == "OPEN" for item in acme_open["items"]))
        self.assertEqual(len(acme_open["items"]), 1)

        acme_september = invoices.list_invoices(self.conn, 1, period="2026-09")
        self.assertEqual([item["id"] for item in acme_september["items"]], [101])

        globex = invoices.list_invoices(self.conn, 2)
        self.assertTrue(all(item["tenant_id"] == 2 for item in globex["items"]))
        self.assertNotIn(101, [item["id"] for item in globex["items"]])

    def test_get_invoice_cannot_cross_tenants(self):
        billing.run_billing(self.conn, "2026-10")
        globex_invoice = self.conn.execute(
            "SELECT id FROM invoices WHERE tenant_id = 2 AND period = '2026-10'"
        ).fetchone()["id"]
        self.assertIsNone(invoices.get_invoice(self.conn, 1, globex_invoice))
        self.assertIsNotNone(invoices.get_invoice(self.conn, 2, globex_invoice))

    def test_usage_aggregation_is_not_per_tenant(self):
        for tenant_id in range(10, 16):
            self.conn.execute(
                "INSERT INTO tenants (id, slug, name, tax_rate_bps) VALUES (?, ?, ?, 0)",
                (tenant_id, f"tenant-{tenant_id}", f"Tenant {tenant_id}"),
            )
            self.conn.execute(
                "INSERT INTO subscriptions "
                "(id, tenant_id, plan_code, status, current_period_start, current_period_end) "
                "VALUES (?, ?, 'starter', 'ACTIVE', '2026-11-01', '2026-12-01')",
                (tenant_id, tenant_id),
            )
            self.conn.execute(
                "INSERT INTO usage_events (tenant_id, metric, quantity, recorded_at) "
                "VALUES (?, 'api_calls', 10, '2026-11-10T10:00:00Z')",
                (tenant_id,),
            )
        self.conn.commit()

        statements = []

        def trace(statement):
            statements.append(statement)

        self.conn.set_trace_callback(trace)
        billing.run_billing(self.conn, "2026-11")
        self.conn.set_trace_callback(None)

        usage_selects = [
            statement
            for statement in statements
            if "USAGE_EVENTS" in statement.upper()
            and "SELECT" in statement.upper()
        ]
        self.assertLessEqual(
            len(usage_selects),
            1,
            f"expected one aggregate usage query, got {len(usage_selects)}",
        )

    def test_existing_suite_still_passes(self):
        backend = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=backend,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
