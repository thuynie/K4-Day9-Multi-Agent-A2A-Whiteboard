from decimal import Decimal

from ..models import DeliveryAnalysis, PaymentAnalysis, PolicyDecision


def decide(order_status: str, payment: PaymentAnalysis, delivery: DeliveryAnalysis) -> PolicyDecision:
    late = delivery.delivery_variance_hours is not None and delivery.delivery_variance_hours > 0
    if order_status == "canceled" and payment.payment_total > 0:
        return PolicyDecision("canceled_order_paid", "ORDER_CANCELED_AFTER_PAYMENT", "platform", ("OLIST_PLATFORM",), payment.payment_total, "issue_full_refund")
    if order_status == "unavailable" and payment.payment_total > 0:
        return PolicyDecision("unavailable_order_paid", "ORDER_UNAVAILABLE_AFTER_PAYMENT", "platform", ("OLIST_PLATFORM",), payment.payment_total, "issue_full_refund")
    if late and delivery.late_handoff_seller_ids:
        return PolicyDecision("late_delivery_seller", "SELLER_HANDOFF_AFTER_LIMIT", "seller", delivery.late_handoff_seller_ids, payment.freight_total, "refund_freight")
    if late:
        return PolicyDecision("late_delivery_logistics", "CARRIER_DELIVERED_AFTER_ESTIMATE", "logistics_provider", ("LOGISTICS_PROVIDER",), payment.freight_total, "refund_freight")
    if payment.payment_row_count >= 2 and payment.reconciled:
        return PolicyDecision("valid_split_payment", "MULTIPLE_PAYMENTS_RECONCILED", None, (), Decimal("0.00"), "explain_valid_split_payment")
    if not late and payment.reconciled:
        return PolicyDecision("unsupported_late_claim", "DELIVERY_WITHIN_ESTIMATE", None, (), Decimal("0.00"), "reject_late_refund")
    raise ValueError("Facts không khớp policy EC_POLICY_V2")
