import unittest

from app import db, invoices, seed


class InvoiceTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        db.init_schema(self.conn)
        seed.seed(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_list_returns_tenant_invoice_shape(self):
        page = invoices.list_invoices(self.conn, 1)
        self.assertEqual(page["items"][0]["id"], 101)
        self.assertEqual(page["items"][0]["tenant_name"], "Acme Robotics")
        self.assertEqual(page["items"][0]["period"], "2026-09")
        self.assertIn("next_cursor", page)

    def test_get_returns_own_invoice(self):
        invoice = invoices.get_invoice(self.conn, 1, 101)
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice["total_cents"], 21750)


if __name__ == "__main__":
    unittest.main()
