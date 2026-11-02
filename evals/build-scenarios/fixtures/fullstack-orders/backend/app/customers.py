from app.models import PageResponse


def list_customers(repo, offset: int = 0, limit: int = 20) -> PageResponse:
    orders = repo.list_orders()
    total = len(orders)
    page = orders[offset : offset + limit]
    item_map = repo.get_items_many([order.id for order in page])
    items = [
        {
            "id": order.id,
            "customer": order.customer,
            "item_count": sum(item.qty for item in item_map[order.id]),
        }
        for order in page
    ]
    return PageResponse(items=items, total=total, offset=offset, limit=limit)
