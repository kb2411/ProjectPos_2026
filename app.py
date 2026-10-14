
import tkinter as tk
from tkinter import ttk

from database import initialize_database, get_all_products


def main():
    # Initialize SQLite database
    initialize_database()

    # Create main window
    root = tk.Tk()
    root.title("ProjectPos_2026 - POS System")
    root.geometry("900x600")

    main_frame = ttk.Frame(root, padding=25)
    main_frame.pack(fill="both", expand=True)

    # Application title
    title_label = ttk.Label(
        main_frame,
        text="Supermarket POS System",
        font=("Arial", 22, "bold")
    )
    title_label.pack(pady=(10, 15))

    # Main function buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame,
        text="Process Sale",
        state="disabled"
    ).pack(side="left", padx=10)

    ttk.Button(
        button_frame,
        text="Handle Returns",
        state="disabled"
    ).pack(side="left", padx=10)

    # Product catalog
    catalog_label = ttk.Label(
        main_frame,
        text="Product Catalog",
        font=("Arial", 16, "bold")
    )
    catalog_label.pack(pady=(25, 10))

    columns = ("id", "name", "price", "stock")

    product_table = ttk.Treeview(
        main_frame,
        columns=columns,
        show="headings",
        height=10
    )

    product_table.heading("id", text="Product ID")
    product_table.heading("name", text="Product Name")
    product_table.heading("price", text="Unit Price")
    product_table.heading("stock", text="Stock")

    product_table.column("id", width=100, anchor="center")
    product_table.column("name", width=220, anchor="center")
    product_table.column("price", width=120, anchor="center")
    product_table.column("stock", width=100, anchor="center")

    product_table.pack(fill="both", expand=True)

    # Load products from database
    products = get_all_products()

    for product_id, name, price_cents, stock in products:
        product_table.insert(
            "",
            "end",
            values=(
                product_id,
                name,
                f"¥{price_cents / 100:.2f}",
                stock
            )
        )

    # Status bar
    status_label = ttk.Label(
        main_frame,
        text=f"Loaded {len(products)} products successfully.",
        font=("Arial", 10)
    )
    status_label.pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    main()
