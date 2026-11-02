import subprocess
import sys
import unittest
from pathlib import Path

from app.orders import list_orders
from app.repository import seed_repo


class HiddenOrdersTest(unittest.TestCase):
    def test_filters_customer_and_status_with_pagination(self):
        page = list_orders(seed_repo(), customer="acme", status="PAID", offset=0, limit=1)
        self.assertEqual(page.total, 2)
        self.assertEqual(len(page.items), 1)
        self.assertEqual(page.items[0]["customer"], "Acme")
        self.assertEqual(page.items[0]["status"], "PAID")
        self.assertEqual(page.next_offset, 1)

    def test_uses_batch_item_lookup(self):
        repo = seed_repo()
        list_orders(repo, limit=3)
        self.assertEqual(repo.get_items_many_calls, 1, "expected batch item lookup")
        self.assertLessEqual(repo.get_items_calls, 1, "avoid per-order item queries")

    def test_item_count_matches_seed_data(self):
        page = list_orders(seed_repo(), limit=1)
        self.assertEqual(page.items[0]["item_count"], 3)

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
