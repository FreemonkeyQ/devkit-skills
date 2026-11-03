import unittest

from app import billing, db, seed


class BillingTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        db.init_schema(self.conn)
        seed.seed(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_generates_one_invoice_per_active_subscription(self):
        result = billing.run_billing(self.conn, "2026-10")
        self.assertEqual(result["created"], 3)
        rows = self.conn.execute(
            "SELECT tenant_id, usage_units, total_cents FROM invoices WHERE period = '2026-10'"
        ).fetchall()
        by_tenant = {row["tenant_id"]: row for row in rows}
        self.assertEqual(by_tenant[2]["usage_units"], 900)
        self.assertEqual(by_tenant[2]["total_cents"], 5255)

    def test_invoice_lines_sum_to_subtotal(self):
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
        for row in rows:
            self.assertEqual(row["subtotal_cents"], row["line_total"])


if __name__ == "__main__":
    unittest.main()
