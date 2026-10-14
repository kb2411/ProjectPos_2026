
import re
import sqlite3
import tkinter as tk
from decimal import Decimal
from tkinter import ttk, messagebox

from database import initialize_database, get_all_products
from cart import Product, ShoppingCart
from sale_service import SaleService
from return_service import ReturnService


def format_money(cents):
    """Convert integer cents to a currency string."""
    return f"¥{cents // 100}.{cents % 100:02d}"


def parse_cash_amount(text):
    """Convert a cash amount to integer cents safely."""
    value = text.strip()

    if not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        raise ValueError(
            "Enter a valid cash amount, such as 30 or 30.50."
        )

    return int(Decimal(value) * 100)



def main():
    # Initialize database
    initialize_database()

    # Initialize business services
    sale_service = SaleService()
    return_service = ReturnService()

    # Initialize shopping cart
    cart = ShoppingCart()

    # Store product information
    products = {}

    roducts = {}
    
    # Main application window
    root = tk.Tk()
    root.title("ProjectPos_2026 - POS System")
    root.geometry("1150x700")
    root.minsize(980, 580)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)

    title_label = ttk.Label(
        main_frame,
        text="Supermarket POS System",
        font=("Arial", 22, "bold")
    )
    title_label.pack(pady=(5, 15))

    # Navigation area
    navigation = ttk.Frame(main_frame)
    navigation.pack(pady=(0, 15))

    ttk.Button(
        navigation,
        text="Process Sale",
        command=lambda: cash_entry.focus_set()
    ).pack(side="left", padx=10)

    ttk.Button(
        navigation,
        text="Handle Returns",
        command=lambda: open_return_window()
    ).pack(side="left", padx=10)

    # Two-column content area
    content = ttk.Frame(main_frame)
    content.pack(fill="both", expand=True)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=2)
    content.rowconfigure(0, weight=1)

    # =========================
    # LEFT: Product Catalog
    # =========================

    left_panel = ttk.LabelFrame(
        content,
        text="Product Catalog",
        padding=12
    )
    left_panel.grid(
        row=0,
        column=0,
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

    for column, heading in [
        ("id", "ID"),
        ("name", "Product Name"),
        ("price", "Unit Price"),
        ("stock", "Stock")
    ]:
        product_table.heading(column, text=heading)

    product_table.column("id", width=55, anchor="center")
    product_table.column("name", width=160, anchor="center")
    product_table.column("price", width=100, anchor="center")
    product_table.column("stock", width=80, anchor="center")

    product_table.pack(fill="both", expand=True)

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

    # =========================
    # RIGHT: Shopping Cart
    # =========================

    right_panel = ttk.LabelFrame(
        content,
        text="Shopping Cart",
        padding=12
    )
    right_panel.grid(
        row=0,
        column=1,
        sticky="nsew"
    )

    cart_columns = ("name", "qty", "subtotal")

    cart_table = ttk.Treeview(
        right_panel,
        columns=cart_columns,
        show="headings",
        selectmode="browse",
        height=10
    )

    cart_table.heading("name", text="Product")
    cart_table.heading("qty", text="Quantity")
    cart_table.heading("subtotal", text="Subtotal")

    cart_table.column("name", width=125, anchor="center")
    cart_table.column("qty", width=70, anchor="center")
    cart_table.column("subtotal", width=110, anchor="center")

    cart_table.pack(fill="both", expand=True)

    total_var = tk.StringVar(value="Total: ¥0.00")

    ttk.Label(
        right_panel,
        textvariable=total_var,
        font=("Arial", 16, "bold")
    ).pack(anchor="e", pady=12)

    cart_controls = ttk.Frame(right_panel)
    cart_controls.pack(fill="x", pady=(0, 12))

    # =========================
    # CASH PAYMENT AREA
    # =========================

    payment_frame = ttk.LabelFrame(
        right_panel,
        text="Cash Payment",
        padding=12
    )
    payment_frame.pack(fill="x", pady=(8, 0))

    ttk.Label(
        payment_frame,
        text="Cash Received (¥):"
    ).grid(row=0, column=0, padx=5, pady=8)

    cash_var = tk.StringVar()

    cash_entry = ttk.Entry(
        payment_frame,
        textvariable=cash_var,
        width=15
    )
    cash_entry.grid(row=0, column=1, padx=5, pady=8)

    status_var = tk.StringVar(value="System ready.")

    # =========================
    # REFRESH FUNCTIONS
    # =========================

    def refresh_product_catalog():
        """Reload products and current stock from SQLite."""
        rows = get_all_products()

        products.clear()

        for row in rows:
            product = Product(*row)
            products[product.product_id] = product

        for item_id in product_table.get_children():
            product_table.delete(item_id)

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

    def refresh_cart():
        """Update cart table and total amount."""
        for item_id in cart_table.get_children():
            cart_table.delete(item_id)

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

    # =========================
    # SHOPPING CART ACTIONS
    # =========================

    def add_selected_product():
        selected = product_table.selection()

        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a product."
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
            messagebox.showerror(
                "Cannot Add Product",
                str(error)
            )
            return

        refresh_cart()
        quantity_var.set("1")

        status_var.set(
            f"Added {product.name} to shopping cart."
        )

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

    def clear_cart():
        cart.clear()
        refresh_cart()
        status_var.set("Shopping cart cleared.")

    # =========================
    # RECEIPT DISPLAY
    # =========================

    def show_receipt(receipt):
        receipt_window = tk.Toplevel(root)
        receipt_window.title(
            f"Sale Receipt #{receipt.sale_id}"
        )
        receipt_window.geometry("460x480")

        receipt_text = tk.Text(
            receipt_window,
            font=("Consolas", 11),
            padx=15,
            pady=15,
            wrap="word"
        )
        receipt_text.pack(fill="both", expand=True)

        lines = [
            "SUPERMARKET POS RECEIPT",
            "=" * 40,
            f"Transaction ID: {receipt.sale_id}",
            "-" * 40
        ]

        for line in receipt.lines:
            lines.append(
                f"{line.name} x {line.quantity}"
                f" @ {format_money(line.unit_price_cents)}"
            )
            lines.append(
                f"    Subtotal: "
                f"{format_money(line.subtotal_cents)}"
            )

        lines.extend([
            "-" * 40,
            f"TOTAL: {format_money(receipt.total_cents)}",
            f"CASH: {format_money(receipt.cash_received_cents)}",
            f"CHANGE: {format_money(receipt.change_cents)}",
            "=" * 40,
            "Thank you for shopping!"
        ])

        receipt_text.insert(
            "1.0",
            "\n".join(lines)
        )

        receipt_text.configure(state="disabled")

        ttk.Button(
            receipt_window,
            text="Close",
            command=receipt_window.destroy
        ).pack(pady=10)

    
    # =========================
    # RETURN MANAGEMENT WINDOW
    # =========================

    def open_return_window():
        return_window = tk.Toplevel(root)
        return_window.title("Handle Returns - POS System")
        return_window.geometry("900x560")
        return_window.minsize(780, 480)

        frame = ttk.Frame(return_window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Handle Returns",
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))

        # Sale lookup area
        search_frame = ttk.LabelFrame(
            frame,
            text="Find Original Sale",
            padding=12
        )
        search_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            search_frame,
            text="Original Sale ID:"
        ).pack(side="left", padx=5)

        sale_id_var = tk.StringVar()

        ttk.Entry(
            search_frame,
            textvariable=sale_id_var,
            width=15
        ).pack(side="left", padx=8)

        # Returned items table
        columns = (
            "name",
            "price",
            "purchased",
            "returned",
            "remaining"
        )

        return_table = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=10
        )

        headings = {
            "name": "Product",
            "price": "Unit Price",
            "purchased": "Purchased",
            "returned": "Returned",
            "remaining": "Remaining"
        }

        for column, heading in headings.items():
            return_table.heading(column, text=heading)
            return_table.column(
                column,
                width=130,
                anchor="center"
            )

        return_table.pack(
            fill="both",
            expand=True,
            pady=(0, 15)
        )

        # Quantity selection
        action_frame = ttk.LabelFrame(
            frame,
            text="Process Return",
            padding=12
        )
        action_frame.pack(fill="x")

        ttk.Label(
            action_frame,
            text="Return Quantity:"
        ).pack(side="left", padx=5)

        return_qty_var = tk.StringVar(value="1")

        ttk.Entry(
            action_frame,
            textvariable=return_qty_var,
            width=10
        ).pack(side="left", padx=8)

        # Window status
        return_status_var = tk.StringVar(
            value="Enter a sale ID to search."
        )

        ttk.Label(
            frame,
            textvariable=return_status_var
        ).pack(anchor="w", pady=(12, 0))

        # State of the currently loaded sale
        current_sale_id = None
        items_by_id = {}

        def lookup_sale():
            nonlocal current_sale_id

            current_sale_id = None
            items_by_id.clear()

            for row_id in return_table.get_children():
                return_table.delete(row_id)

            raw_id = sale_id_var.get().strip()

            if not raw_id.isdecimal() or int(raw_id) <= 0:
                messagebox.showerror(
                    "Invalid Sale ID",
                    "Please enter a positive sale ID.",
                    parent=return_window
                )
                return

            sale_id = int(raw_id)

            try:
                items = return_service.get_returnable_items(
                    sale_id
                )
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror(
                    "Sale Lookup Failed",
                    str(error),
                    parent=return_window
                )
                return

            current_sale_id = sale_id

            for item in items:
                item_id = item["sale_item_id"]
                items_by_id[item_id] = item

                return_table.insert(
                    "",
                    "end",
                    iid=str(item_id),
                    values=(
                        item["product_name"],
                        format_money(
                            item["unit_price_cents"]
                        ),
                        item["purchased_quantity"],
                        item["returned_quantity"],
                        item["remaining_quantity"]
                    )
                )

            return_status_var.set(
                f"Loaded sale #{sale_id}. "
                f"Select an item to return."
            )

        def confirm_return():
            if current_sale_id is None:
                messagebox.showwarning(
                    "Sale Required",
                    "Please look up a sale first.",
                    parent=return_window
                )
                return

            # Prevent using a different, unsearched sale ID
            if sale_id_var.get().strip() != str(current_sale_id):
                messagebox.showwarning(
                    "Lookup Required",
                    "Sale ID changed. Please search again.",
                    parent=return_window
                )
                return

            selected = return_table.selection()

            if not selected:
                messagebox.showwarning(
                    "Item Required",
                    "Please select a returned product.",
                    parent=return_window
                )
                return

            try:
                quantity = int(return_qty_var.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Invalid Quantity",
                    "Enter a valid integer quantity.",
                    parent=return_window
                )
                return

            if quantity <= 0:
                messagebox.showerror(
                    "Invalid Quantity",
                    "Return quantity must be positive.",
                    parent=return_window
                )
                return

            sale_item_id = int(selected[0])
            item = items_by_id[sale_item_id]

            if quantity > item["remaining_quantity"]:
                messagebox.showerror(
                    "Quantity Exceeded",
                    "Return quantity exceeds the "
                    "remaining returnable quantity.",
                    parent=return_window
                )
                return

            refund_cents = (
                item["unit_price_cents"] * quantity
            )

            confirmed = messagebox.askyesno(
                "Confirm Return",
                f"Product: {item['product_name']}\n"
                f"Quantity: {quantity}\n"
                f"Refund: {format_money(refund_cents)}\n\n"
                "Confirm this return?",
                parent=return_window
            )

            if not confirmed:
                return

            try:
                receipt = return_service.process_return(
                    current_sale_id,
                    sale_item_id,
                    quantity
                )
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror(
                    "Return Failed",
                    str(error),
                    parent=return_window
                )
                return

            # Refresh database-backed GUI information
            refresh_product_catalog()
            lookup_sale()

            return_qty_var.set("1")

            return_status_var.set(
                f"Return #{receipt.return_id} completed."
            )

            status_var.set(
                f"Return #{receipt.return_id} completed. "
                f"Inventory updated."
            )

            messagebox.showinfo(
                "Return Completed",
                f"Return ID: {receipt.return_id}\n"
                f"Original Sale: #{receipt.original_sale_id}\n"
                f"Product: {receipt.product_name}\n"
                f"Quantity: {receipt.quantity}\n"
                f"Refund: {format_money(receipt.refund_cents)}\n"
                f"Remaining Returnable: "
                f"{receipt.remaining_quantity}",
                parent=return_window
            )

        # Action buttons
        ttk.Button(
            search_frame,
            text="Lookup Sale",
            command=lookup_sale
        ).pack(side="left", padx=8)

        ttk.Button(
            action_frame,
            text="Confirm Return",
            command=confirm_return
        ).pack(side="left", padx=12)

        ttk.Button(
            action_frame,
            text="Close",
            command=return_window.destroy
        ).pack(side="right", padx=5)

    
    # =========================
    # CASH PAYMENT PROCESSING
    # =========================

    def process_payment():
        if not cart.lines:
            messagebox.showwarning(
                "Empty Cart",
                "Please add products before payment."
            )
            return

        try:
            cash_cents = parse_cash_amount(
                cash_var.get()
            )
        except ValueError as error:
            messagebox.showerror(
                "Invalid Cash Amount",
                str(error)
            )
            return

        try:
            receipt = sale_service.complete_sale(
                cart,
                cash_cents
            )
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror(
                "Payment Failed",
                str(error)
            )
            return

        # Transaction has committed successfully
        cart.clear()
        refresh_cart()
        refresh_product_catalog()
        cash_var.set("")

        status_var.set(
            f"Sale #{receipt.sale_id} completed successfully."
        )

        show_receipt(receipt)

    # =========================
    # ACTION BUTTONS
    # =========================

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

    ttk.Button(
        payment_frame,
        text="Confirm Payment",
        command=process_payment
    ).grid(
        row=1,
        column=0,
        columnspan=2,
        pady=12
    )

    # Status bar
    ttk.Label(
        main_frame,
        textvariable=status_var
    ).pack(anchor="w", pady=(12, 0))

    # Initial catalog load
    refresh_product_catalog()

    root.mainloop()


if __name__ == "__main__":
    main()
