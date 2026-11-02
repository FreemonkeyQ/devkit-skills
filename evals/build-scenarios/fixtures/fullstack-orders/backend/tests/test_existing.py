import unittest

from app.customers import list_customers
from app.orders import list_orders
from app.repository import seed_repo


class ExistingOrdersTest(unittest.TestCase):
    def test_lists_first_page(self):
        page = list_orders(seed_repo(), limit=2)
        self.assertEqual(page.total, 6)
        self.assertEqual(len(page.items), 2)
        self.assertEqual(page.next_offset, 2)

    def test_customers_use_batch_item_lookup(self):
        repo = seed_repo()
        page = list_customers(repo, limit=2)
        self.assertEqual(page.total, 6)
        self.assertEqual(repo.get_items_many_calls, 1)
        self.assertEqual(repo.get_items_calls, 0)


if __name__ == "__main__":
    unittest.main()
