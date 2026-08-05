from .agents.customer_agent import CustomerAgent
from .agents.delivery_agent import DeliveryAgent
from .agents.order_product_agent import OrderProductAgent
from .agents.payment_agent import PaymentAgent
from .agents.policy_agent import PolicyAgent
from .agents.verifier_agent import VerifierAgent
from .data_repository import DataRepository
from .models import CaseInput
from .observability.trace_writer import TraceWriter
from .output_builder import OutputBuilder


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
        self.output_builder = OutputBuilder(repository)

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

    def process_case(self, case: CaseInput, trace: TraceWriter | None = None) -> dict:
        if trace:
            trace.write(case.case_id, "coordinator", "case_started", "success", {"order_id": case.claimed_order_id})
        facts = self.collect_facts(case.claimed_order_id)
        if trace:
            for agent, key in (
                ("customer_agent", "customer"), ("order_product_agent", "order_context"),
                ("payment_agent", "payment"), ("delivery_agent", "delivery"),
                ("policy_agent", "decision"),
            ):
                trace.write(case.case_id, agent, "handoff_completed", "success", {"result_type": key})
        draft = self.output_builder.build(case, facts)
        errors = self.verifier_agent.verify_draft(case, draft, self.repository)
        if errors:
            if trace:
                trace.write(case.case_id, "verifier_agent", "verification_failed", "error", {"errors": errors})
            raise ValueError(f"{case.case_id}: {'; '.join(errors)}")
        if trace:
            trace.write(case.case_id, "verifier_agent", "verification_passed", "success")
            trace.write(case.case_id, "coordinator", "case_completed", "success")
        return draft
