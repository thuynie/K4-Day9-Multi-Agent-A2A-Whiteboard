from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class CaseInput:
    case_id: str
    claimed_order_id: str
    policy_version: str
    include_customer_history: bool
    include_product_context: bool


@dataclass(frozen=True)
class PaymentAnalysis:
    item_total: Decimal
    freight_total: Decimal
    expected_total: Decimal | None
    payment_total: Decimal
    difference: Decimal | None
    reconciled: bool | None
    payment_types: tuple[str, ...] = field(default_factory=tuple)
    payment_row_count: int = 0


@dataclass(frozen=True)
class DeliveryAnalysis:
    delivered_at: str | None
    estimated_at: str | None
    carrier_handoff_at: str | None
    delivery_variance_hours: Decimal | None
    late_handoff_seller_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyDecision:
    primary_issue: str
    root_cause_code: str
    party_type: str | None
    party_ids: tuple[str, ...]
    recommended_refund: Decimal
    main_action: str
