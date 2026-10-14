
import sqlite3
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "pos.db"


def initialize_database():
    """Create the product table and insert sample data."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0)
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        if count == 0:
            sample_products = [
                ("Milk", 650, 30),
                ("Bread", 800, 25),
                ("Apple", 350, 100),
                ("Rice", 2200, 40)
            ]

            conn.executemany(
                """
                INSERT INTO products
                (name, price_cents, stock)
                VALUES (?, ?, ?)
                """,
                sample_products
            )

        conn.commit()

    finally:
        conn.close()


def get_all_products():
    """Retrieve all products from the database."""

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.execute("""
            SELECT id, name, price_cents, stock
            FROM products
            ORDER BY id
        """)

        return cursor.fetchall()

    finally:
        conn.close()
