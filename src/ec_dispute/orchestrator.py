from .agents.customer_agent import CustomerAgent
from .agents.delivery_agent import DeliveryAgent
from .agents.order_product_agent import OrderProductAgent
from .agents.payment_agent import PaymentAgent
from .agents.policy_agent import PolicyAgent
from .agents.verifier_agent import VerifierAgent
from .data_repository import DataRepository


class Coordinator:
    """Điểm ghép agent; output builder được hoàn thiện ở bước tiếp theo."""

    def __init__(self, repository: DataRepository) -> None:
        self.repository = repository
        self.customer_agent = CustomerAgent()
        self.order_agent = OrderProductAgent()
        self.payment_agent = PaymentAgent()
        self.delivery_agent = DeliveryAgent()
        self.policy_agent = PolicyAgent()
        self.verifier_agent = VerifierAgent()

    def collect_facts(self, order_id: str) -> dict:
        customer = self.customer_agent.investigate(self.repository, order_id)
        order_context = self.order_agent.investigate(self.repository, order_id)
        payment = self.payment_agent.investigate(
            self.repository,
            order_id,
            order_context["item_total_brl"],
            order_context["freight_total_brl"],
            bool(order_context["items"]),
        )
        delivery = self.delivery_agent.investigate(self.repository, order_id)
        decision = self.policy_agent.investigate(order_context["order"]["order_status"], payment, delivery)
        return {
            "customer": customer,
            "order_context": order_context,
            "payment": payment,
            "delivery": delivery,
            "decision": decision,
        }
