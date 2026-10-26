from collections.abc import Sequence


def orders_to_csv(rows: Sequence[tuple[int, str, str]]) -> str:
    lines = ["id,customer,status"]
    lines.extend(f"{order_id},{customer},{status}" for order_id, customer, status in rows)
    return "\n".join(lines) + "\n"
