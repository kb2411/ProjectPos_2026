
import sqlite3
from dataclasses import dataclass

from database import DB_PATH


@dataclass(frozen=True)
class ReceiptLine:
    name: str
    quantity: int
    unit_price_cents: int

    @property
    def subtotal_cents(self):
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class SaleReceipt:
    sale_id: int
    total_cents: int
    cash_received_cents: int
    change_cents: int
    lines: tuple


class SaleService:
    """Handle cash sales and inventory transactions."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def complete_sale(self, cart, cash_received_cents):
        if not cart.lines:
            raise ValueError("Shopping cart is empty.")

        if type(cash_received_cents) is not int:
            raise ValueError("Cash amount must be an integer in cents.")

        if cash_received_cents < 0:
            raise ValueError("Cash amount cannot be negative.")

        conn = sqlite3.connect(self.db_path, timeout=10)

        try:
            conn.execute("PRAGMA foreign_keys = ON")

            # Lock for a consistent read-and-update transaction
            conn.execute("BEGIN IMMEDIATE")

            receipt_lines = []

            # Validate each cart item against current database data
            for line in cart.lines:
                product_id = line.product.product_id
                quantity = line.quantity

                if quantity <= 0:
                    raise ValueError("Invalid product quantity.")

                row = conn.execute(
                    """
                    SELECT name, price_cents, stock
                    FROM products
                    WHERE id = ?
                    """,
                    (product_id,)
                ).fetchone()

                if row is None:
                    raise ValueError("Product no longer exists.")

                name, current_price, stock = row

                if current_price != line.product.price_cents:
                    raise ValueError(
                        f"Price changed for {name}. "
                        "Please restart the sale."
                    )

                if quantity > stock:
                    raise ValueError(
                        f"Insufficient stock for {name}."
                    )

                receipt_lines.append(
                    ReceiptLine(name, quantity, current_price)
                )

            total_cents = sum(
                line.subtotal_cents for line in receipt_lines
            )

            if cash_received_cents < total_cents:
                raise ValueError("Insufficient cash payment.")

            change_cents = cash_received_cents - total_cents

            # Save the sale header
            cursor = conn.execute(
                """
                INSERT INTO sales
                (total_cents, cash_received_cents, change_cents)
                VALUES (?, ?, ?)
                """,
                (total_cents, cash_received_cents, change_cents)
            )

            sale_id = cursor.lastrowid

            # Save sale details and update inventory
            for original_line, receipt_line in zip(
                cart.lines, receipt_lines
            ):
                conn.execute(
                    """
                    INSERT INTO sale_items
                    (sale_id, product_id, product_name,
                     unit_price_cents, quantity, subtotal_cents)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sale_id,
                        original_line.product.product_id,
                        receipt_line.name,
                        receipt_line.unit_price_cents,
                        receipt_line.quantity,
                        receipt_line.subtotal_cents
                    )
                )

                result = conn.execute(
                    """
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ? AND stock >= ?
                    """,
                    (
                        receipt_line.quantity,
                        original_line.product.product_id,
                        receipt_line.quantity
                    )
                )

                if result.rowcount != 1:
                    raise ValueError(
                        "Inventory update failed."
                    )

            # All changes succeed together
            conn.commit()

            return SaleReceipt(
                sale_id=sale_id,
                total_cents=total_cents,
                cash_received_cents=cash_received_cents,
                change_cents=change_cents,
                lines=tuple(receipt_lines)
            )

        except Exception:
            # Any failure cancels all database changes
            conn.rollback()
            raise

        finally:
            conn.close()
