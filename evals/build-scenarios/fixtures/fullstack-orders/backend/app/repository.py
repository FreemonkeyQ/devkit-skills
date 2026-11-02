from app.models import Order, OrderItem


class OrderRepository:
    def __init__(self, orders: list[Order], items: dict[int, list[OrderItem]]):
        self._orders = orders
        self._items = items
        self.get_items_calls = 0
        self.get_items_many_calls = 0

    def list_orders(self, customer: str | None = None, status: str | None = None):
        result = list(self._orders)
        if customer:
            needle = customer.lower()
            result = [order for order in result if needle in order.customer.lower()]
        if status:
            result = [order for order in result if order.status == status]
        return result

    def get_items(self, order_id: int) -> list[OrderItem]:
        self.get_items_calls += 1
        return self._items.get(order_id, [])

    def get_items_many(self, order_ids: list[int]) -> dict[int, list[OrderItem]]:
        self.get_items_many_calls += 1
        return {order_id: self._items.get(order_id, []) for order_id in order_ids}


def seed_repo() -> OrderRepository:
    orders = [
        Order(1, "Acme", "PAID", "2026-01-01T09:00:00Z", [1]),
        Order(2, "Beta", "SHIPPED", "2026-01-02T09:00:00Z", [2]),
        Order(3, "Acme Labs", "SHIPPED", "2026-01-03T09:00:00Z", [3]),
        Order(4, "Gamma", "PAID", "2026-01-04T09:00:00Z", [4]),
        Order(5, "Acme", "PAID", "2026-01-05T09:00:00Z", [5]),
        Order(6, "Beta", "CANCELLED", "2026-01-06T09:00:00Z", [6]),
    ]
    items = {
        1: [OrderItem("A-1", 2), OrderItem("B-1", 1)],
        2: [OrderItem("C-1", 1)],
        3: [OrderItem("D-1", 2)],
        4: [OrderItem("E-1", 1), OrderItem("F-1", 1)],
        5: [OrderItem("G-1", 3)],
        6: [OrderItem("H-1", 1)],
    }
    return OrderRepository(orders, items)
