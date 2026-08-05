from decimal import Decimal

from ..data_repository import DataRepository
from ..utils import money, unique_in_order


class OrderProductAgent:
    name = "order_product_agent"

    def investigate(self, repository: DataRepository, order_id: str) -> dict:
        order = repository.orders[order_id]
        items = sorted(repository.items_by_order.get(order_id, []), key=lambda row: int(row["order_item_id"]))
        product_ids = unique_in_order(row["product_id"] for row in items)
        seller_ids = unique_in_order(row["seller_id"] for row in items)
        categories = unique_in_order(
            repository.products[product_id]["product_category_name"]
            for product_id in product_ids
            if repository.products[product_id]["product_category_name"]
        )
        return {
            "order": order,
            "items": items,
            "product_ids": product_ids[:5],
            "seller_ids": seller_ids[:3],
            "category_names": categories[:5],
            "item_total_brl": money(sum((Decimal(row["price"]) for row in items), Decimal("0"))),
            "freight_total_brl": money(sum((Decimal(row["freight_value"]) for row in items), Decimal("0"))),
        }
