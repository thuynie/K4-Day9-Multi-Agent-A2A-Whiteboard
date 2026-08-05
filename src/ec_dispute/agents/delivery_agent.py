from ..data_repository import DataRepository
from ..models import DeliveryAnalysis, SellerHandoff
from ..utils import hours_between, parse_timestamp, unique_in_order


class DeliveryAgent:
    name = "delivery_agent"

    def investigate(self, repository: DataRepository, order_id: str) -> DeliveryAnalysis:
        order = repository.orders[order_id]
        items = repository.items_by_order.get(order_id, [])
        carrier = order["order_delivered_carrier_date"] or None
        seller_order = unique_in_order(row["seller_id"] for row in items)
        earliest_limit: dict[str, str] = {}
        for item in items:
            seller_id = item["seller_id"]
            current = earliest_limit.get(seller_id)
            if current is None or parse_timestamp(item["shipping_limit_date"]) < parse_timestamp(current):
                earliest_limit[seller_id] = item["shipping_limit_date"]
        handoffs = tuple(
            SellerHandoff(
                seller_id=seller_id,
                shipping_limit_at=earliest_limit[seller_id],
                handoff_variance_hours=hours_between(carrier, earliest_limit[seller_id]),
                late_handoff=(variance := hours_between(carrier, earliest_limit[seller_id])) is not None and variance > 0,
            )
            for seller_id in seller_order
        )
        late_sellers = tuple(value.seller_id for value in handoffs if value.late_handoff)
        delivered = order["order_delivered_customer_date"] or None
        estimated = order["order_estimated_delivery_date"] or None
        return DeliveryAnalysis(
            delivered_at=delivered,
            estimated_at=estimated,
            carrier_handoff_at=carrier,
            delivery_variance_hours=hours_between(delivered, estimated),
            seller_handoff_analysis=handoffs,
            late_handoff_seller_ids=late_sellers,
        )
