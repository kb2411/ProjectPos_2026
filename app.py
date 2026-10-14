
import tkinter as tk
from tkinter import ttk, messagebox

from database import initialize_database, get_all_products
from cart import Product, ShoppingCart


def format_money(cents):
    return f"¥{cents // 100}.{cents % 100:02d}"


def main():
    # Initialize data
    initialize_database()

    product_rows = get_all_products()
    products = {
        row[0]: Product(*row)
        for row in product_rows
    }

    cart = ShoppingCart()

    # Main window
    root = tk.Tk()
    root.title("ProjectPos_2026 - POS System")
    root.geometry("1100x650")
    root.minsize(950, 520)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)

    title = ttk.Label(
        main_frame,
        text="Supermarket POS System",
        font=("Arial", 22, "bold")
    )
    title.pack(pady=(5, 15))

    # Navigation
    navigation = ttk.Frame(main_frame)
    navigation.pack(pady=(0, 20))

    ttk.Button(
        navigation,
        text="Process Sale",
        state="disabled"
    ).pack(side="left", padx=10)

    ttk.Button(
        navigation,
        text="Handle Returns",
        state="disabled"
    ).pack(side="left", padx=10)

    # Two-column layout
    content = ttk.Frame(main_frame)
    content.pack(fill="both", expand=True)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=2)
    content.rowconfigure(0, weight=1)

    # Product catalog
    left_panel = ttk.LabelFrame(
        content,
        text="Product Catalog",
        padding=12
    )
    left_panel.grid(
        row=0, column=0,
        sticky="nsew",
        padx=(0, 10)
    )

    product_columns = ("id", "name", "price", "stock")

    product_table = ttk.Treeview(
        left_panel,
        columns=product_columns,
        show="headings",
        selectmode="browse",
        height=12
    )

    for col, heading in [
        ("id", "ID"),
        ("name", "Product Name"),
        ("price", "Unit Price"),
        ("stock", "Stock")
    ]:
        product_table.heading(col, text=heading)

    product_table.column("id", width=55, anchor="center")
    product_table.column("name", width=160, anchor="center")
    product_table.column("price", width=100, anchor="center")
    product_table.column("stock", width=80, anchor="center")

    product_table.pack(fill="both", expand=True)

    for product in products.values():
        product_table.insert(
            "",
            "end",
            iid=str(product.product_id),
            values=(
                product.product_id,
                product.name,
                format_money(product.price_cents),
                product.stock
            )
        )

    # Product controls
    product_controls = ttk.Frame(left_panel)
    product_controls.pack(fill="x", pady=(12, 0))

    ttk.Label(
        product_controls,
        text="Quantity:"
    ).pack(side="left")

    quantity_var = tk.StringVar(value="1")

    quantity_entry = ttk.Entry(
        product_controls,
        textvariable=quantity_var,
        width=8
    )
    quantity_entry.pack(side="left", padx=8)

    # Shopping cart
    right_panel = ttk.LabelFrame(
        content,
        text="Shopping Cart",
        padding=12
    )
    right_panel.grid(
        row=0, column=1,
        sticky="nsew"
    )

    cart_columns = ("name", "qty", "subtotal")

    cart_table = ttk.Treeview(
        right_panel,
        columns=cart_columns,
        show="headings",
        selectmode="browse",
        height=12
    )

    cart_table.heading("name", text="Product")
    cart_table.heading("qty", text="Quantity")
    cart_table.heading("subtotal", text="Subtotal")

    cart_table.column("name", width=130, anchor="center")
    cart_table.column("qty", width=75, anchor="center")
    cart_table.column("subtotal", width=115, anchor="center")

    cart_table.pack(fill="both", expand=True)

    total_var = tk.StringVar(value="Total: ¥0.00")

    total_label = ttk.Label(
        right_panel,
        textvariable=total_var,
        font=("Arial", 16, "bold")
    )
    total_label.pack(anchor="e", pady=15)

    cart_controls = ttk.Frame(right_panel)
    cart_controls.pack(fill="x")

    status_var = tk.StringVar(
        value=f"Loaded {len(products)} products."
    )

    # Refresh shopping cart display
    def refresh_cart():
        for row_id in cart_table.get_children():
            cart_table.delete(row_id)

        for line in cart.lines:
            cart_table.insert(
                "",
                "end",
                iid=str(line.product.product_id),
                values=(
                    line.product.name,
                    line.quantity,
                    format_money(line.subtotal_cents)
                )
            )

        total_var.set(
            f"Total: {format_money(cart.total_cents)}"
        )

    # Add selected product
    def add_selected_product():
        selected = product_table.selection()

        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a product first."
            )
            return

        try:
            quantity = int(quantity_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "Invalid Quantity",
                "Please enter a valid integer."
            )
            return

        product_id = int(selected[0])
        product = products[product_id]

        try:
            cart.add_product(product, quantity)
        except ValueError as error:
            messagebox.showerror("Cannot Add Product", str(error))
            return

        refresh_cart()
        quantity_var.set("1")
        status_var.set(f"Added {product.name} to shopping cart.")

    # Remove selected cart item
    def remove_selected_product():
        selected = cart_table.selection()

        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select an item from the cart."
            )
            return

        product_id = int(selected[0])
        cart.remove_product(product_id)
        refresh_cart()
        status_var.set("Selected item removed.")

    # Clear the shopping cart
    def clear_cart():
        cart.clear()
        refresh_cart()
        status_var.set("Shopping cart cleared.")

    ttk.Button(
        product_controls,
        text="Add to Cart",
        command=add_selected_product
    ).pack(side="left", padx=8)

    ttk.Button(
        cart_controls,
        text="Remove Selected",
        command=remove_selected_product
    ).pack(side="left", padx=4)

    ttk.Button(
        cart_controls,
        text="Clear Cart",
        command=clear_cart
    ).pack(side="left", padx=4)

    # Status bar
    ttk.Label(
        main_frame,
        textvariable=status_var
    ).pack(anchor="w", pady=(12, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
