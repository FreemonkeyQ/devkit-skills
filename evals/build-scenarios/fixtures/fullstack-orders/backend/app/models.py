from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderItem:
    sku: str
    qty: int


@dataclass
class Order:
    id: int
    customer: str
    status: str
    created_at: str
    item_ids: list[int] = field(default_factory=list)


@dataclass
class PageResponse:
    items: list[dict]
    total: int
    offset: int
    limit: int

    @property
    def next_offset(self):
        next_value = self.offset + len(self.items)
        return next_value if next_value < self.total else None
