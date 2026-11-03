import unittest

from app.money import micros_to_cents, tax_cents


class MoneyTest(unittest.TestCase):
    def test_micros_round_half_up(self):
        self.assertEqual(micros_to_cents(3_999_600), 400)
        self.assertEqual(micros_to_cents(166_650), 17)

    def test_tax_round_half_up(self):
        self.assertEqual(tax_cents(20300, 875), 1776)
        self.assertEqual(tax_cents(4900, 725), 355)


if __name__ == "__main__":
    unittest.main()
