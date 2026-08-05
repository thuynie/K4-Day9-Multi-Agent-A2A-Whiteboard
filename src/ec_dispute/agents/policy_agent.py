from ..models import DeliveryAnalysis, PaymentAnalysis, PolicyDecision
from ..policies.ec_policy_v2 import decide


class PolicyAgent:
    name = "policy_agent"

    def investigate(self, order_status: str, payment: PaymentAnalysis, delivery: DeliveryAnalysis) -> PolicyDecision:
        return decide(order_status, payment, delivery)
