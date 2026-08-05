from ..data_repository import DataRepository


class CustomerAgent:
    name = "customer_agent"

    def investigate(self, repository: DataRepository, order_id: str) -> dict:
        order = repository.orders[order_id]
        customer = repository.customers[order["customer_id"]]
        unique_id = customer["customer_unique_id"]
        related = [value for value in repository.orders_by_unique_customer[unique_id] if value != order_id]
        return {"customer_unique_id": unique_id, "related_order_ids": related[:5]}
