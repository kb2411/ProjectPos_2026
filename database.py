
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "pos.db"


def initialize_database(db_path=DB_PATH):
    """Initialize all required POS database tables."""

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        # Product information
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL
                    CHECK(price_cents >= 0),
                stock INTEGER NOT NULL
                    CHECK(stock >= 0)
            )
        """)

        # Completed sales
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_cents INTEGER NOT NULL,
                cash_received_cents INTEGER NOT NULL,
                change_cents INTEGER NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Items belonging to each sale
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                unit_price_cents INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal_cents INTEGER NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Insert sample products only if empty
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


def get_all_products(db_path=DB_PATH):
    """Return all available product records."""

    conn = sqlite3.connect(db_path)

    try:
        return conn.execute("""
            SELECT id, name, price_cents, stock
            FROM products
            ORDER BY id
        """).fetchall()

    finally:
        conn.close()
