
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cart import Product, ShoppingCart
from database import initialize_database, get_all_products
from sale_service import SaleService
from return_service import ReturnService


class TestReturnService(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_pos.db"

        initialize_database(self.db_path)

        self.sale_service = SaleService(self.db_path)
        self.return_service = ReturnService(self.db_path)

        rows = get_all_products(self.db_path)
        products = {
            row[0]: Product(*row)
            for row in rows
        }

        cart = ShoppingCart()
        cart.add_product(products[1], 2)

        # Original sale: 2 bottles of Milk
        self.sale = self.sale_service.complete_sale(
            cart, 2000
        )

        items = self.return_service.get_returnable_items(
            self.sale.sale_id
        )

        self.sale_item_id = items[0]["sale_item_id"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def get_stock(self):
        conn = sqlite3.connect(self.db_path)

        try:
            return conn.execute(
                "SELECT stock FROM products WHERE id = 1"
            ).fetchone()[0]
        finally:
            conn.close()

    def test_partial_return(self):
        receipt = self.return_service.process_return(
            self.sale.sale_id,
            self.sale_item_id,
            1
        )

        self.assertEqual(receipt.refund_cents, 650)
        self.assertEqual(receipt.remaining_quantity, 1)
        self.assertEqual(self.get_stock(), 29)

    def test_return_quantity_limit(self):
        # Only 2 units were purchased
        with self.assertRaises(ValueError):
            self.return_service.process_return(
                self.sale.sale_id,
                self.sale_item_id,
                3
            )

        # Failed return must not change inventory
        self.assertEqual(self.get_stock(), 28)

        conn = sqlite3.connect(self.db_path)

        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM return_transactions"
            ).fetchone()[0]

            self.assertEqual(count, 0)
        finally:
            conn.close()

    def test_prevent_duplicate_returns(self):
        # Return both purchased units
        self.return_service.process_return(
            self.sale.sale_id,
            self.sale_item_id,
            2
        )

        self.assertEqual(self.get_stock(), 30)

        # Further returns must be rejected
        with self.assertRaises(ValueError):
            self.return_service.process_return(
                self.sale.sale_id,
                self.sale_item_id,
                1
            )

        self.assertEqual(self.get_stock(), 30)

    def test_invalid_sale_id(self):
        with self.assertRaises(ValueError):
            self.return_service.get_returnable_items(99999)


if __name__ == "__main__":
    unittest.main()
