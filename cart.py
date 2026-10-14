
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    price_cents: int
    stock: int


@dataclass
class CartLine:
    product: Product
    quantity: int

    @property
    def subtotal_cents(self):
        return self.product.price_cents * self.quantity


class ShoppingCart:
    def __init__(self):
        self._items = {}

    def add_product(self, product, quantity):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        product_id = product.product_id
        existing = self._items.get(product_id)

        current_quantity = existing.quantity if existing else 0
        new_quantity = current_quantity + quantity

        if new_quantity > product.stock:
            raise ValueError(
                f"Insufficient stock for {product.name}. "
                f"Available: {product.stock}, requested: {new_quantity}."
            )

        if existing:
            existing.quantity = new_quantity
        else:
            self._items[product_id] = CartLine(product, quantity)

    def remove_product(self, product_id):
        if product_id in self._items:
            del self._items[product_id]

    def clear(self):
        self._items.clear()

    @property
    def lines(self):
        return tuple(self._items.values())

    @property
    def total_cents(self):
        return sum(
            item.subtotal_cents for item in self._items.values()
        )
