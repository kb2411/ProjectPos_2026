
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cart import Product, ShoppingCart
from database import initialize_database, get_all_products
from sale_service import SaleService


class TestSaleService(unittest.TestCase):

    def setUp(self):
        # Isolated test database
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_pos.db"

        initialize_database(self.db_path)
        self.service = SaleService(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_cart(self):
        rows = get_all_products(self.db_path)

        products = {
            row[0]: Product(*row)
            for row in rows
        }

        cart = ShoppingCart()
        return cart, products

    def test_successful_cash_sale(self):
        cart, products = self.create_cart()

        cart.add_product(products[1], 2)
        cart.add_product(products[2], 1)

        receipt = self.service.complete_sale(cart, 3000)

        self.assertEqual(receipt.total_cents, 2100)
        self.assertEqual(receipt.change_cents, 900)

        conn = sqlite3.connect(self.db_path)

        try:
            milk_stock = conn.execute(
                "SELECT stock FROM products WHERE id = 1"
            ).fetchone()[0]

            sale_count = conn.execute(
                "SELECT COUNT(*) FROM sales"
            ).fetchone()[0]

            detail_count = conn.execute(
                "SELECT COUNT(*) FROM sale_items"
            ).fetchone()[0]

            self.assertEqual(milk_stock, 28)
            self.assertEqual(sale_count, 1)
            self.assertEqual(detail_count, 2)

        finally:
            conn.close()

    def test_insufficient_cash_rolls_back(self):
        cart, products = self.create_cart()
        cart.add_product(products[1], 2)

        with self.assertRaises(ValueError):
            self.service.complete_sale(cart, 100)

        conn = sqlite3.connect(self.db_path)

        try:
            stock = conn.execute(
                "SELECT stock FROM products WHERE id = 1"
            ).fetchone()[0]

            sale_count = conn.execute(
                "SELECT COUNT(*) FROM sales"
            ).fetchone()[0]

            self.assertEqual(stock, 30)
            self.assertEqual(sale_count, 0)

        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
