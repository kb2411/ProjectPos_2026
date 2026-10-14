
import sqlite3
from dataclasses import dataclass

from database import DB_PATH


@dataclass(frozen=True)
class ReturnReceipt:
    return_id: int
    original_sale_id: int
    product_name: str
    quantity: int
    refund_cents: int
    remaining_quantity: int


class ReturnService:
    """Manage returns against original sale records."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_returnable_items(self, sale_id):
        """Find purchased items and remaining returnable quantities."""

        if type(sale_id) is not int or sale_id <= 0:
            raise ValueError("Invalid sale ID.")

        conn = sqlite3.connect(self.db_path)

        try:
            sale = conn.execute(
                "SELECT id FROM sales WHERE id = ?",
                (sale_id,)
            ).fetchone()

            if sale is None:
                raise ValueError("Original sale not found.")

            rows = conn.execute("""
                SELECT
                    si.id,
                    si.product_name,
                    si.unit_price_cents,
                    si.quantity,
                    COALESCE(
                        (
                            SELECT SUM(ri.quantity)
                            FROM return_items ri
                            WHERE ri.sale_item_id = si.id
                        ),
                        0
                    ) AS returned_quantity
                FROM sale_items si
                WHERE si.sale_id = ?
                ORDER BY si.id
            """, (sale_id,)).fetchall()

            results = []

            for item_id, name, price, purchased, returned in rows:
                results.append({
                    "sale_item_id": item_id,
                    "product_name": name,
                    "unit_price_cents": price,
                    "purchased_quantity": purchased,
                    "returned_quantity": returned,
                    "remaining_quantity": purchased - returned
                })

            return results

        finally:
            conn.close()

    def process_return(self, sale_id, sale_item_id, quantity):
        """Record a return and restore inventory atomically."""

        if type(sale_id) is not int or sale_id <= 0:
            raise ValueError("Invalid sale ID.")

        if type(sale_item_id) is not int or sale_item_id <= 0:
            raise ValueError("Invalid sale item ID.")

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Return quantity must be positive.")

        conn = sqlite3.connect(self.db_path, timeout=10)

        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN IMMEDIATE")

            # Find the item from the original sale
            item = conn.execute("""
                SELECT
                    product_id,
                    product_name,
                    unit_price_cents,
                    quantity
                FROM sale_items
                WHERE id = ? AND sale_id = ?
            """, (sale_item_id, sale_id)).fetchone()

            if item is None:
                raise ValueError("Sale item not found.")

            product_id, name, unit_price, purchased = item

            # Count quantities already returned
            returned = conn.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM return_items
                WHERE sale_item_id = ?
            """, (sale_item_id,)).fetchone()[0]

            remaining = purchased - returned

            if quantity > remaining:
                raise ValueError(
                    f"Return quantity exceeds the remaining "
                    f"returnable quantity ({remaining})."
                )

            refund_cents = unit_price * quantity

            # Create a return transaction
            cursor = conn.execute("""
                INSERT INTO return_transactions
                (original_sale_id, refund_cents)
                VALUES (?, ?)
            """, (sale_id, refund_cents))

            return_id = cursor.lastrowid

            # Store returned item details
            conn.execute("""
                INSERT INTO return_items
                (return_id, sale_item_id, product_id,
                 quantity, unit_price_cents, subtotal_cents)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                return_id,
                sale_item_id,
                product_id,
                quantity,
                unit_price,
                refund_cents
            ))

            # Restore inventory
            result = conn.execute("""
                UPDATE products
                SET stock = stock + ?
                WHERE id = ?
            """, (quantity, product_id))

            if result.rowcount != 1:
                raise ValueError("Inventory restoration failed.")

            conn.commit()

            return ReturnReceipt(
                return_id=return_id,
                original_sale_id=sale_id,
                product_name=name,
                quantity=quantity,
                refund_cents=refund_cents,
                remaining_quantity=remaining - quantity
            )

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()
