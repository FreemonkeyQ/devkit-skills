import argparse
import json

from app.orders import list_orders
from app.repository import seed_repo


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    orders = subparsers.add_parser("orders")
    orders.add_argument("--customer")
    orders.add_argument("--status")
    orders.add_argument("--offset", type=int, default=0)
    orders.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.command == "orders":
        page = list_orders(
            seed_repo(),
            customer=args.customer,
            status=args.status,
            offset=args.offset,
            limit=args.limit,
        )
        print(
            json.dumps(
                {
                    "items": page.items,
                    "total": page.total,
                    "next_offset": page.next_offset,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
