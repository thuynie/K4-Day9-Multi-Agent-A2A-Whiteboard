from __future__ import annotations

from decimal import Decimal

from .data_repository import DataRepository
from .models import CaseInput, DeliveryAnalysis, PaymentAnalysis, PolicyDecision
from .utils import unique_in_order


def decimal_value(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


class OutputBuilder:
    def __init__(self, repository: DataRepository) -> None:
        self.repository = repository

    def build(self, case: CaseInput, facts: dict) -> dict:
        order_context = facts["order_context"]
        customer = facts["customer"]
        payment: PaymentAnalysis = facts["payment"]
        delivery: DeliveryAnalysis = facts["delivery"]
        decision: PolicyDecision = facts["decision"]
        order_id = case.claimed_order_id
        items = order_context["items"]
        payments = sorted(
            self.repository.payments_by_order.get(order_id, []),
            key=lambda row: int(row["payment_sequential"]),
        )

        secondary = self._secondary_issues(customer, order_context, payment)
        actions = self._actions(decision, secondary)
        item_ids = [f"{order_id}:{row['order_item_id']}" for row in items][:5]
        payment_ids = [f"{order_id}:{row['payment_sequential']}" for row in payments][:5]
        evidence = self._evidence(order_id, item_ids, payment_ids, decision)

        responsible = []
        if decision.party_type:
            responsible = [
                {"party_type": decision.party_type, "party_id": party_id}
                for party_id in decision.party_ids[:3]
            ]

        return {
            "case_id": case.case_id,
            "case_assessment": {
                "primary_issue": decision.primary_issue,
                "secondary_issues": secondary,
                "case_status": "action_required" if decision.recommended_refund > 0 else "no_action",
                "confidence": 1.0,
            },
            "affected_entities": {
                "order_ids": [order_id],
                "item_ids": item_ids,
                "seller_ids": order_context["seller_ids"][:3],
                "payment_ids": payment_ids,
            },
            "customer_context": {
                "customer_unique_id": customer["customer_unique_id"],
                "related_order_ids": customer["related_order_ids"][:5],
            },
            "product_context": {
                "product_ids": order_context["product_ids"][:5],
                "category_names": order_context["category_names"][:5],
            },
            "delivery_analysis": {
                "delivered_at": delivery.delivered_at,
                "estimated_delivery_at": delivery.estimated_at,
                "carrier_handoff_at": delivery.carrier_handoff_at,
                "delivery_variance_hours": decimal_value(delivery.delivery_variance_hours),
                "seller_handoff_analysis": [
                    {
                        "seller_id": value.seller_id,
                        "shipping_limit_at": value.shipping_limit_at,
                        "handoff_variance_hours": decimal_value(value.handoff_variance_hours),
                        "late_handoff": value.late_handoff,
                    }
                    for value in delivery.seller_handoff_analysis[:3]
                ],
                "late_handoff_seller_ids": list(delivery.late_handoff_seller_ids[:3]),
            },
            "payment_reconciliation": {
                "currency": "BRL",
                "item_total_brl": decimal_value(payment.item_total),
                "freight_total_brl": decimal_value(payment.freight_total),
                "expected_total_brl": decimal_value(payment.expected_total),
                "payment_total_brl": decimal_value(payment.payment_total),
                "difference_brl": decimal_value(payment.difference),
                "reconciled": payment.reconciled,
                "payment_types": list(payment.payment_types),
            },
            "root_cause_analysis": {
                "ranked_causes": [{"cause_code": decision.root_cause_code, "rank": 1}],
                "responsible_parties": responsible,
            },
            "evidence_ids": evidence[:20],
            "financial_resolution": {
                "currency": "BRL",
                "recommended_refund_brl": decimal_value(decision.recommended_refund),
            },
            "resolution_actions": actions[:5],
        }

    @staticmethod
    def _secondary_issues(customer: dict, order_context: dict, payment: PaymentAnalysis) -> list[str]:
        issues: list[str] = []
        items = order_context["items"]
        if len(items) >= 2:
            issues.append("multi_item_order")
        if len(unique_in_order(row["seller_id"] for row in items)) >= 2:
            issues.append("multi_seller_order")
        if payment.payment_row_count >= 2:
            issues.append("split_payment")
        if customer["related_order_ids"]:
            issues.append("repeat_customer")
        if len(order_context["category_names"]) >= 2:
            issues.append("multiple_categories")
        return issues

    @staticmethod
    def _actions(decision: PolicyDecision, secondary: list[str]) -> list[str]:
        actions = [decision.main_action]
        if decision.primary_issue == "late_delivery_seller":
            actions.append("review_seller_handoff")
        elif decision.primary_issue == "late_delivery_logistics":
            actions.append("review_carrier_delay")
        if decision.recommended_refund > 0:
            actions.append("verify_refund_completion")
        if "multi_seller_order" in secondary:
            actions.append("coordinate_multi_seller_case")
        if "split_payment" in secondary and decision.primary_issue != "valid_split_payment":
            actions.append("verify_payment_allocation")
        return actions

    @staticmethod
    def _evidence(order_id: str, item_ids: list[str], payment_ids: list[str], decision: PolicyDecision) -> list[str]:
        evidence = [f"order:{order_id}"]
        evidence.extend(f"item:{value}" for value in item_ids)
        evidence.extend(f"payment:{value}" for value in payment_ids)
        if decision.party_type == "seller":
            evidence.extend(f"seller:{seller_id}" for seller_id in decision.party_ids[:3])
        evidence.append(f"policy:{decision.root_cause_code}")
        return evidence
