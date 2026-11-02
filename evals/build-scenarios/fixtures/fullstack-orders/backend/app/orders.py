from app.models import PageResponse


def list_orders(
    repo,
    customer: str | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> PageResponse:
    matched = repo.list_orders(status=status)
    total = len(matched)
    page = matched[offset : offset + limit]
    items = []
    for order in page:
        line_items = repo.get_items(order.id)
        items.append(
            {
                "id": order.id,
                "customer": order.customer,
                "status": order.status,
                "item_count": sum(item.qty for item in line_items),
                "created_at": order.created_at,
            }
        )
    return PageResponse(items=items, total=total, offset=offset, limit=limit)
